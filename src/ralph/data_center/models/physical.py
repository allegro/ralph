# -*- coding: utf-8 -*-
import logging
import re
from collections import namedtuple, OrderedDict
from itertools import chain

from dj.choices import Choices, Country
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator
)
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Region
from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.admin.helpers import generate_html_link
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.assets.models.assets import Asset, NamedMixin
from ralph.assets.models.choices import AssetSource
from ralph.assets.models.components import Ethernet
from ralph.assets.utils import DNSaaSPublisherMixin, move_parents_models
from ralph.back_office.helpers import dc_asset_to_bo_asset_status_converter
from ralph.back_office.models import BackOfficeAsset, Warehouse
from ralph.data_center.models.choices import (
    ConnectionType,
    DataCenterAssetStatus,
    Orientation,
    RackOrientation
)
from ralph.data_center.models.mixins import WithManagementIPMixin
from ralph.data_center.publishers import publish_host_update
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, PreviousStateMixin
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import Transition
from ralph.networks.models import IPAddress, Network, NetworkEnvironment
from ralph.signals import post_commit

logger = logging.getLogger(__name__)

# i.e. number in range 1-16 and optional postfix 'A' or 'B'
VALID_SLOT_NUMBER_FORMAT = re.compile("^([1-9][A,B]?|1[0-6][A,B]?)$")

ACCESSORY_DATA = [
    "brush",
    "patch_panel_fc",
    "patch_panel_utp",
    "organizer",
    "power_socket",
]


def assign_additional_hostname_choices(actions, objects):
    """
    Generate choices with networks common for each object.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list of tuples with available network choices
    """
    networks = []
    for obj in objects:
        networks.append(set(obj._get_available_networks()))
    networks = set.intersection(*networks)
    choices = [(str(net.pk), net) for net in networks]
    return choices


class Gap(object):
    """A placeholder that represents a gap in a blade chassis"""

    id = 0
    barcode = "-"
    sn = "-"
    service = namedtuple("Service", ["name"])("-")
    model = namedtuple("Model", ["name"])("-")
    linked_device = None

    def __init__(self, slot_no, orientation):
        self.slot_no = slot_no
        self.orientation = orientation

    def get_orientation_desc(self):
        return self.orientation

    def get_absolute_url(self):
        return ""

    @classmethod
    def generate_gaps(cls, items):
        def get_number(slot_no):
            """Returns the integer part of slot number"""
            m = re.match(r"(\d+)", slot_no)
            return (m and int(m.group(0))) or 0

        if not items:
            return []
        max_slot_no = max([get_number(asset.slot_no) for asset in items])
        first_asset_slot_no = items[0].slot_no
        ab = first_asset_slot_no and first_asset_slot_no[-1] in {"A", "B"}
        slot_nos = {asset.slot_no for asset in items}

        def handle_missing(slot_no):
            if slot_no not in slot_nos:
                items.append(Gap(slot_no, items[0].get_orientation_desc()))

        for slot_no in range(1, max_slot_no + 1):
            if ab:
                for letter in ["A", "B"]:
                    handle_missing(str(slot_no) + letter)
            else:
                handle_missing(str(slot_no))
        return items


class DataCenterType(Choices):
    _ = Choices.Choice

    dc = _("dc")
    cowork = _("cowork")
    call_center = _("callcenter")
    depot = _("depot")
    warehouse = _("warehouse")
    retail = _("retail")
    office = _("office")


class DataCenter(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    _allow_in_dashboard = True

    show_on_dashboard = models.BooleanField(default=True)

    company = models.CharField(
        verbose_name=_("company"), max_length=256, blank=True, null=True
    )
    country = models.PositiveIntegerField(
        verbose_name=_("country"), choices=Country(), blank=True, null=True
    )
    city = models.CharField(
        verbose_name=_("city"), max_length=256, blank=True, null=True
    )
    address = models.CharField(
        verbose_name=_("address"), max_length=256, blank=True, null=True
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    type = models.PositiveIntegerField(
        verbose_name=_("data center type"),
        choices=DataCenterType(),
        blank=True,
        null=True,
    )
    shortcut = models.CharField(
        verbose_name=_("shortcut"), max_length=256, blank=True, null=True
    )

    @property
    def rack_set(self):
        return Rack.objects.select_related("server_room").filter(
            server_room__data_center=self
        )

    @property
    def server_rooms(self):
        return ServerRoom.objects.filter(data_center=self)

    def __str__(self):
        return self.name


class ServerRoomManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("data_center")
            .prefetch_related("racks")
        )


class ServerRoom(AdminAbsoluteUrlMixin, NamedMixin.NonUnique, models.Model):
    _allow_in_dashboard = True

    data_center = models.ForeignKey(
        DataCenter, verbose_name=_("data center"), on_delete=models.CASCADE
    )
    data_center._autocomplete = False
    data_center._filter_title = _("data center")
    visualization_cols_num = models.PositiveIntegerField(
        verbose_name=_("visualization grid columns number"),
        default=20,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),  # is correlate with $grid-count
        ],
    )
    visualization_rows_num = models.PositiveIntegerField(
        verbose_name=_("visualization grid rows number"),
        default=20,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),  # is correlate with $grid-count
        ],
    )
    objects = ServerRoomManager()

    def __str__(self):
        return "{} ({})".format(self.name, self.data_center.name)


class Accessory(AdminAbsoluteUrlMixin, NamedMixin):
    class Meta:
        verbose_name = _("accessory")
        verbose_name_plural = _("accessories")


class RackAccessory(AdminAbsoluteUrlMixin, models.Model):
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    rack = models.ForeignKey("Rack", on_delete=models.CASCADE)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )
    position = models.IntegerField(null=True, blank=False)
    remarks = models.CharField(
        verbose_name="Additional remarks",
        max_length=1024,
        blank=True,
    )

    class Meta:
        verbose_name_plural = _("rack accessories")

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

    def __str__(self):
        rack_name = self.rack.name if self.rack else ""
        accessory_name = self.accessory.name if self.accessory else ""
        return "{rack_name} - {accessory_name}".format(
            rack_name=rack_name,
            accessory_name=accessory_name,
        )


class RackManager(models.Manager):
    pass

    def get_queryset(self):
        return super().get_queryset().select_related("server_room__data_center")


class Rack(AdminAbsoluteUrlMixin, NamedMixin.NonUnique, models.Model):
    _allow_in_dashboard = True

    objects = RackManager()

    server_room = models.ForeignKey(
        ServerRoom,
        verbose_name=_("server room"),
        null=True,
        blank=False,
        related_name="racks",
        on_delete=models.CASCADE,
    )
    server_room._autocomplete = False
    server_room._filter_title = _("server room")
    description = models.CharField(_("description"), max_length=250, blank=True)
    orientation = models.PositiveIntegerField(
        choices=RackOrientation(),
        default=RackOrientation.top.id,
    )
    max_u_height = models.IntegerField(default=48)

    visualization_col = models.PositiveIntegerField(
        verbose_name=_("column number on visualization grid"),
        default=0,
    )
    visualization_row = models.PositiveIntegerField(
        verbose_name=_("row number on visualization grid"),
        default=0,
    )
    accessories = models.ManyToManyField(Accessory, through="RackAccessory")
    require_position = models.BooleanField(
        default=True,
        help_text=_(
            "Uncheck if position is optional for this rack (ex. when rack "
            "has warehouse-kind role"
        ),
    )
    reverse_ordering = models.BooleanField(
        default=settings.RACK_LISTING_NUMBERING_TOP_TO_BOTTOM,
        help_text=_(
            "Check if RU numbers count from top to bottom with position 1 "
            "starting at the top of the rack. If unchecked position 1 is "
            "at the bottom of the rack"
        ),
        verbose_name=_("RU order top to bottom"),
    )

    class Meta:
        unique_together = ("name", "server_room")

    def __str__(self):
        if self.server_room:
            return "{} ({}/{})".format(
                self.name,
                self.server_room.data_center,
                self.server_room.name,
            )
        return self.name

    def get_orientation_desc(self):
        return RackOrientation.name_from_id(self.orientation)

    def get_root_assets(self, side=None):
        filter_kwargs = {
            "rack": self,
        }
        if side:
            filter_kwargs["orientation"] = side
        else:
            filter_kwargs["orientation__in"] = [Orientation.front, Orientation.back]
        return (
            DataCenterAsset.objects.select_related("model__category")
            .filter(Q(slot_no="") | Q(slot_no=None), **filter_kwargs)
            .exclude(model__has_parent=True)
        )

    def get_free_u(self):
        u_list = [True] * self.max_u_height
        accessories = RackAccessory.objects.values_list("position").filter(rack=self)
        dc_assets = self.get_root_assets().values_list(
            "position", "model__height_of_device"
        )

        def fill_u_list(objects, height_of_device=lambda obj: 1):
            for obj in objects:
                # if position is None when objects simply does not have
                # (assigned) position and position 0 is for some
                # accessories (pdu) with left-right orientation and
                # should not be included in free/filled space.
                if obj[0] == 0 or obj[0] is None:
                    continue

                start = obj[0] - 1
                end = min(self.max_u_height, obj[0] + int(height_of_device(obj)) - 1)
                height = end - start
                if height:
                    u_list[start:end] = [False] * height

        fill_u_list(accessories)
        fill_u_list(dc_assets, lambda obj: obj[1])
        return sum(u_list)

    def get_pdus(self):
        return DataCenterAsset.objects.select_related("model").filter(
            rack=self,
            orientation__in=(Orientation.left, Orientation.right),
            position=0,
        )


class NetworkableBaseObject(models.Model):
    # TODO: hostname field and not-abstract cls
    custom_fields_inheritance = OrderedDict(
        [
            ("configuration_path", "assets.ConfigurationClass"),
            ("configuration_path__module", "assets.ConfigurationModule"),
            ("service_env", "assets.ServiceEnvironment"),
        ]
    )

    @cached_property
    def network_environment(self):
        """
        Return first found network environment for this `DataCenterAsset` based
        on assigned rack.

        Full algorithm:
            * find networks which are "connected" to rack assigned to me
            * find all (distinct) network environments assigned to these
              networks
            * filter networks by ips currently assigned to object,
            * return first founded network environment if there is any,
              otherwise return `None`
        """
        if self.rack_id:
            # TODO: better handling (when server in multiple environments)
            return (
                NetworkEnvironment.objects.filter(
                    network__racks=self.rack,
                    # filter env by ips assigned to current object
                    network__in=self.ipaddresses.filter(
                        is_management=False
                    ).values_list("network", flat=True),
                )
                .distinct()
                .first()
            )

    @property
    def ipaddresses(self):
        return IPAddress.objects.filter(ethernet__base_object=self)

    def get_next_free_hostname(self):
        """
        Returns next free hostname for this asset based on Rack's network
        environment (hostnaming template).
        """
        if self.network_environment:
            return self.network_environment.next_free_hostname
        logger.warning("Network-environment not provided for %s", self)
        return ""

    def issue_next_free_hostname(self):
        """
        Reserve next (currently) free hostname and return it. You should assign
        this hostname to asset manually (or do with it whatever you like).
        """
        if self.network_environment:
            return self.network_environment.issue_next_free_hostname()
        logger.warning("Network-environment not provided for %s", self)
        return ""

    def _get_available_network_environments(self):
        if self.rack_id:
            return list(
                NetworkEnvironment.objects.filter(
                    network__racks=self.rack_id
                ).distinct()
            )
        return NetworkEnvironment.objects.none()

    def _get_available_networks(self, as_query=False, is_broadcasted_in_dhcp=False):
        if self.rack_id:
            query = Network.objects.filter(racks=self.rack_id).distinct()
        else:
            query = Network.objects.none()
        if is_broadcasted_in_dhcp:
            query = query.filter(dhcp_broadcast=True)

        return query if as_query else list(query)

    class Meta:
        abstract = True


class DataCenterAsset(
    PreviousStateMixin,
    DNSaaSPublisherMixin,
    WithManagementIPMixin,
    NetworkableBaseObject,
    AutocompleteTooltipMixin,
    Asset,
):
    _allow_in_dashboard = True

    previous_dc_host_update_fields = ["hostname"]

    rack = models.ForeignKey(Rack, null=True, blank=False, on_delete=models.PROTECT)
    status = TransitionField(
        default=DataCenterAssetStatus.new.id,
        choices=DataCenterAssetStatus(),
    )
    position = models.IntegerField(null=True, blank=True)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )
    vendor_contract_number = models.CharField(
        null=True,
        blank=True,
        max_length=256,
        verbose_name=_("Vendor contract number"),
    )
    leasing_rate = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Leasing rate"),
    )
    slot_no = models.CharField(
        blank=True,
        help_text=_("Fill it if asset is blade server"),
        max_length=3,
        null=True,
        validators=[
            RegexValidator(
                regex=VALID_SLOT_NUMBER_FORMAT,
                message=_(
                    "Slot number should be a number from range 1-16 with "
                    "an optional postfix 'A' or 'B' (e.g. '16A')"
                ),
                code="invalid_slot_no",
            )
        ],
        verbose_name=_("slot number"),
    )
    firmware_version = models.CharField(
        null=True,
        blank=True,
        max_length=256,
        verbose_name=_("firmware version"),
    )
    bios_version = models.CharField(
        null=True,
        blank=True,
        max_length=256,
        verbose_name=_("BIOS version"),
    )
    connections = models.ManyToManyField(
        "self",
        through="Connection",
        symmetrical=False,
    )
    source = models.PositiveIntegerField(
        blank=True,
        choices=AssetSource(),
        db_index=True,
        null=True,
        verbose_name=_("source"),
    )
    delivery_date = models.DateField(null=True, blank=True)
    production_year = models.PositiveSmallIntegerField(null=True, blank=True)
    production_use_date = models.DateField(null=True, blank=True)

    autocomplete_tooltip_fields = [
        "rack",
        "barcode",
        "sn",
    ]
    _summary_fields = [
        ("hostname", "Hostname"),
        ("location", "Location"),
        ("model__name", "Model"),
    ]

    class Meta:
        verbose_name = _("data center asset")
        verbose_name_plural = _("data center assets")
        abstract = False

    def __str__(self):
        return "{} (BC: {} / SN: {})".format(
            self.hostname or "-", self.barcode or "-", self.sn or "-"
        )

    def __repr__(self):
        return "<DataCenterAsset: {}>".format(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk:
            # When changing rack we search and save all descendants
            if self._previous_state["rack_id"] != self.rack_id:
                DataCenterAsset.objects.filter(parent=self).update(rack=self.rack)
            # When changing position if is blade,
            # we search and save all descendants
            if self._previous_state["position"] != self.position:
                DataCenterAsset.objects.filter(parent=self).update(
                    position=self.position
                )

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

    def get_location(self):
        location = []
        if self.rack:
            location.extend(
                [
                    self.rack.server_room.data_center.name,
                    self.rack.server_room.name,
                    self.rack.name,
                ]
            )
        if self.position:
            location.append(str(self.position))
        if self.slot_no:
            location.append(str(self.slot_no))
        return location

    @property
    def is_blade(self):
        if self.model_id and self.model.has_parent:
            return True
        return False

    @property
    def cores_count(self):
        """Returns cores count assigned to device in Ralph"""
        asset_cores_count = self.model.cores_count if self.model else 0
        return asset_cores_count

    @cached_property
    def location(self):
        """
        Additional column 'location' display filter by:
        data center, server_room, rack, position (if is blade)
        """
        base_url = reverse("admin:data_center_datacenterasset_changelist")
        position = self.position
        if self.is_blade:
            position = generate_html_link(
                base_url,
                label=position,
                params={
                    "rack": self.rack_id,
                    "position__start": self.position,
                    "position__end": self.position,
                },
            )

        result = (
            [
                generate_html_link(
                    base_url,
                    label=self.rack.server_room.data_center.name,
                    params={
                        "rack__server_room__data_center": self.rack.server_room.data_center_id
                    },
                ),
                generate_html_link(
                    base_url,
                    label=self.rack.server_room.name,
                    params={"rack__server_room": self.rack.server_room_id},
                ),
                generate_html_link(
                    base_url,
                    label=self.rack.name,
                    params={"rack": self.rack_id},
                ),
            ]
            if self.rack and self.rack.server_room
            else []
        )

        if self.position:
            result.append(str(position))
        if self.slot_no:
            result.append(str(self.slot_no))

        return "&nbsp;/&nbsp;".join(result) if self.rack else "&mdash;"

    def _validate_orientation(self):
        """
        Validate if orientation is valid for given position.
        """
        if self.position is None:
            return
        if self.position == 0 and not Orientation.is_width(self.orientation):
            msg = "Valid orientations for picked position are: {}".format(
                ", ".join(choice.desc for choice in Orientation.WIDTH.choices)
            )
            raise ValidationError({"orientation": [msg]})
        if self.position > 0 and not Orientation.is_depth(self.orientation):
            msg = "Valid orientations for picked position are: {}".format(
                ", ".join(choice.desc for choice in Orientation.DEPTH.choices)
            )
            raise ValidationError({"orientation": [msg]})

    def _validate_position(self):
        """
        Validate if position not empty when rack requires it.
        """
        if self.rack and self.position is None and self.rack.require_position:
            msg = "Position is required for this rack"
            raise ValidationError({"position": [msg]})

    def _validate_position_in_rack(self):
        """
        Validate if position is in rack height range.
        """
        if (
            self.rack
            and self.position is not None
            and self.position > self.rack.max_u_height
        ):
            msg = 'Position is higher than "max u height" = {}'.format(
                self.rack.max_u_height,
            )
            raise ValidationError({"position": [msg]})
        if self.position is not None and self.position < 0:
            msg = "Position should be 0 or greater"
            raise ValidationError({"position": msg})

    def _validate_slot_no(self):
        if self.model_id:
            if self.model.has_parent and not self.slot_no:
                raise ValidationError(
                    {"slot_no": "Slot number is required when asset is blade"}
                )
            if not self.model.has_parent and self.slot_no:
                raise ValidationError(
                    {
                        "slot_no": (
                            "Slot number cannot be filled when asset is not blade"
                        )
                    }
                )
            if self.parent:
                dc_asset_with_slot_no = (
                    DataCenterAsset.objects.filter(
                        parent=self.parent,
                        slot_no=self.slot_no,
                        orientation=self.orientation,
                    )
                    .exclude(pk=self.pk)
                    .first()
                )
                if dc_asset_with_slot_no:
                    message = mark_safe(
                        (
                            "Slot is already occupied by: "
                            '<a href="{}" target="_blank">{}</a>'
                        ).format(
                            reverse(
                                "admin:data_center_datacenterasset_change",
                                args=[dc_asset_with_slot_no.id],
                            ),
                            dc_asset_with_slot_no,
                        )
                    )
                    raise ValidationError({"slot_no": message})

    def clean(self):
        # TODO: this should be default logic of clean method;
        # we could register somehow validators (or take each func with
        # _validate prefix) and call it here
        errors = {}
        for validator in [
            super().clean,
            self._validate_orientation,
            self._validate_position,
            self._validate_position_in_rack,
            self._validate_slot_no,
        ]:
            try:
                validator()
            except ValidationError as e:
                e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)

    def get_related_assets(self):
        """Returns the children of a blade chassis"""
        orientations = [Orientation.front, Orientation.back]
        assets_by_orientation = []
        for orientation in orientations:
            assets_by_orientation.append(
                list(
                    DataCenterAsset.objects.select_related("model")
                    .filter(
                        parent=self,
                        orientation=orientation,
                        model__has_parent=True,
                    )
                    .exclude(id=self.id)
                )
            )
        assets = [Gap.generate_gaps(assets) for assets in assets_by_orientation]
        return chain(*assets)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(status=DataCenterAssetStatus.liquidated.id)

    @classmethod
    @transition_action(
        verbose_name=_("Change rack"),
        form_fields={
            "rack": {
                "field": forms.CharField(
                    widget=AutocompleteWidget(field=rack, admin_site=ralph_site)
                ),
            }
        },
    )
    def change_rack(cls, instances, **kwargs):
        rack = Rack.objects.get(pk=kwargs["rack"])
        for instance in instances:
            instance.rack = rack

    @classmethod
    @transition_action(
        verbose_name=_("Convert to BackOffice Asset"),
        disable_save_object=True,
        only_one_action=True,
        form_fields={
            "warehouse": {
                "field": forms.CharField(label=_("Warehouse")),
                "autocomplete_field": "warehouse",
                "autocomplete_model": "back_office.BackOfficeAsset",
            },
            "region": {
                "field": forms.CharField(label=_("Region")),
                "autocomplete_field": "region",
                "autocomplete_model": "back_office.BackOfficeAsset",
            },
        },
    )
    def convert_to_backoffice_asset(cls, instances, **kwargs):
        with transaction.atomic():
            for i, instance in enumerate(instances):
                back_office_asset = BackOfficeAsset()

                back_office_asset.region = Region.objects.get(pk=kwargs["region"])
                back_office_asset.warehouse = Warehouse.objects.get(
                    pk=kwargs["warehouse"]
                )
                target_status = int(
                    Transition.objects.values_list("target", flat=True).get(
                        pk=kwargs["transition_id"]
                    )  # noqa
                )
                back_office_asset.status = dc_asset_to_bo_asset_status_converter(  # noqa
                    instance.status, target_status
                )
                move_parents_models(
                    instance, back_office_asset, exclude_copy_fields=["status"]
                )
                # Save new asset to list, required to redirect url.
                # RunTransitionView.get_success_url()
                instances[i] = back_office_asset

    @classmethod
    @transition_action(
        verbose_name=_("Cleanup scm status"),
    )
    def cleanup_scm_statuscheck(cls, instances, **kwargs):
        with transaction.atomic():
            for instance in instances:
                try:
                    instance.scmstatuscheck.delete()
                except DataCenterAsset.scmstatuscheck.RelatedObjectDoesNotExist:
                    pass

    @classmethod
    @transition_action(
        verbose_name=_("Assign additional IP and hostname pair"),
        form_fields={
            "network_pk": {
                "field": forms.ChoiceField(label=_("Select network")),
                "choices": assign_additional_hostname_choices,
                "exclude_from_history": True,
            },
        },
    )
    def assign_additional_hostname(cls, instances, network_pk, **kwargs):
        """
        Assign new hostname for instances based on selected network.
        """
        network = Network.objects.get(pk=network_pk)
        env = network.network_environment
        with transaction.atomic():
            for instance in instances:
                ethernet = Ethernet.objects.create(base_object=instance)
                ethernet.ipaddress = network.issue_next_free_ip()
                ethernet.ipaddress.hostname = env.issue_next_free_hostname()
                ethernet.ipaddress.save()
                ethernet.save()


class Connection(AdminAbsoluteUrlMixin, models.Model):
    outbound = models.ForeignKey(
        "DataCenterAsset",
        verbose_name=_("connected to device"),
        on_delete=models.PROTECT,
        related_name="outbound_connections",
    )
    inbound = models.ForeignKey(
        "DataCenterAsset",
        verbose_name=_("connected device"),
        on_delete=models.PROTECT,
        related_name="inbound_connections",
    )
    # TODO: discuss
    connection_type = models.PositiveIntegerField(
        verbose_name=_("connection type"), choices=ConnectionType()
    )

    def __str__(self):
        return "%s -> %s (%s)" % (self.outbound, self.inbound, self.connection_type)


post_commit(publish_host_update, DataCenterAsset)
