# -*- coding: utf-8 -*-
import logging
import re
from collections import namedtuple
from itertools import chain

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Region
from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.admin.helpers import generate_html_link
from ralph.admin.sites import ralph_site
from ralph.admin.widgets import AutocompleteWidget
from ralph.assets.models.assets import Asset, NamedMixin
from ralph.assets.models.choices import AssetSource
from ralph.assets.utils import move_parents_models
from ralph.back_office.models import BackOfficeAsset, Warehouse
from ralph.data_center.models.choices import (
    ConnectionType,
    DataCenterAssetStatus,
    Orientation,
    RackOrientation
)
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.networks.models import IPAddress, Network, NetworkEnvironment

logger = logging.getLogger(__name__)

# i.e. number in range 1-16 and optional postfix 'A' or 'B'
VALID_SLOT_NUMBER_FORMAT = re.compile('^([1-9][A,B]?|1[0-6][A,B]?)$')

ACCESSORY_DATA = [
    'brush', 'patch_panel_fc', 'patch_panel_utp', 'organizer', 'power_socket'
]


class Gap(object):
    """A placeholder that represents a gap in a blade chassis"""

    id = 0
    barcode = '-'
    sn = '-'
    service = namedtuple('Service', ['name'])('-')
    model = namedtuple('Model', ['name'])('-')
    linked_device = None

    def __init__(self, slot_no, orientation):
        self.slot_no = slot_no
        self.orientation = orientation

    def get_orientation_desc(self):
        return self.orientation

    def get_absolute_url(self):
        return ''

    @classmethod
    def generate_gaps(cls, items):
        def get_number(slot_no):
            """Returns the integer part of slot number"""
            m = re.match(r'(\d+)', slot_no)
            return (m and int(m.group(0))) or 0
        if not items:
            return []
        max_slot_no = max([
            get_number(asset.slot_no)
            for asset in items
        ])
        first_asset_slot_no = items[0].slot_no
        ab = first_asset_slot_no and first_asset_slot_no[-1] in {'A', 'B'}
        slot_nos = {asset.slot_no for asset in items}

        def handle_missing(slot_no):
            if slot_no not in slot_nos:
                items.append(Gap(slot_no, items[0].get_orientation_desc()))

        for slot_no in range(1, max_slot_no + 1):
            if ab:
                for letter in ['A', 'B']:
                    handle_missing(str(slot_no) + letter)
            else:
                handle_missing(str(slot_no))
        return items


class DataCenter(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    _allow_in_dashboard = True

    visualization_cols_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid columns number'),
        default=20,
    )
    visualization_rows_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid rows number'),
        default=20,
    )
    show_on_dashboard = models.BooleanField(default=True)

    @property
    def rack_set(self):
        return Rack.objects.select_related(
            'server_room'
        ).filter(server_room__data_center=self)

    @property
    def server_rooms(self):
        return ServerRoom.objects.filter(data_center=self)

    def __str__(self):
        return self.name


class ServerRoom(NamedMixin.NonUnique, models.Model):
    _allow_in_dashboard = True

    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))
    data_center._autocomplete = False
    data_center._filter_title = _('data center')

    def __str__(self):
        return '{} ({})'.format(self.name, self.data_center.name)


class Accessory(NamedMixin):

    class Meta:
        verbose_name = _('accessory')
        verbose_name_plural = _('accessories')


class RackAccessory(AdminAbsoluteUrlMixin, models.Model):
    accessory = models.ForeignKey(Accessory)
    rack = models.ForeignKey('Rack')
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )
    position = models.IntegerField(null=True, blank=False)
    remarks = models.CharField(
        verbose_name='Additional remarks',
        max_length=1024,
        blank=True,
    )

    class Meta:
        verbose_name_plural = _('rack accessories')

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

    def __str__(self):
        rack_name = self.rack.name if self.rack else ''
        accessory_name = self.accessory.name if self.accessory else ''
        return '{rack_name} - {accessory_name}'.format(
            rack_name=rack_name, accessory_name=accessory_name,
        )


class Rack(AdminAbsoluteUrlMixin, NamedMixin.NonUnique, models.Model):
    _allow_in_dashboard = True

    server_room = models.ForeignKey(
        ServerRoom, verbose_name=_('server room'),
        null=True,
        blank=True,
    )
    server_room._autocomplete = False
    server_room._filter_title = _('server room')
    description = models.CharField(
        _('description'), max_length=250, blank=True
    )
    orientation = models.PositiveIntegerField(
        choices=RackOrientation(),
        default=RackOrientation.top.id,
    )
    max_u_height = models.IntegerField(default=48)

    visualization_col = models.PositiveIntegerField(
        verbose_name=_('column number on visualization grid'),
        default=0,
    )
    visualization_row = models.PositiveIntegerField(
        verbose_name=_('row number on visualization grid'),
        default=0,
    )
    accessories = models.ManyToManyField(Accessory, through='RackAccessory')
    require_position = models.BooleanField(
        default=True,
        help_text=_(
            'Uncheck if position is optional for this rack (ex. when rack '
            'has warehouse-kind role'
        )
    )

    class Meta:
        unique_together = ('name', 'server_room')

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
            'rack': self,
        }
        if side:
            filter_kwargs['orientation'] = side
        else:
            filter_kwargs['orientation__in'] = [
                Orientation.front, Orientation.back
            ]
        return DataCenterAsset.objects.select_related(
            'model', 'model__category'
        ).filter(
            Q(slot_no='') | Q(slot_no=None), **filter_kwargs
        ).exclude(model__has_parent=True)

    def get_free_u(self):
        u_list = [True] * self.max_u_height
        accessories = RackAccessory.objects.values_list(
            'position').filter(rack=self)
        dc_assets = self.get_root_assets().values_list(
            'position', 'model__height_of_device'
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
                end = min(
                    self.max_u_height, obj[0] + int(height_of_device(obj)) - 1
                )
                height = end - start
                if height:
                    u_list[start:end] = [False] * height
        fill_u_list(accessories)
        fill_u_list(dc_assets, lambda obj: obj[1])
        return sum(u_list)

    def get_pdus(self):
        return DataCenterAsset.objects.select_related('model').filter(
            rack=self,
            orientation__in=(Orientation.left, Orientation.right),
            position=0,
        )


class DataCenterAsset(AutocompleteTooltipMixin, Asset):
    _allow_in_dashboard = True

    rack = models.ForeignKey(Rack, null=True, blank=True)
    status = TransitionField(
        default=DataCenterAssetStatus.new.id,
        choices=DataCenterAssetStatus(),
    )
    position = models.IntegerField(null=True, blank=True)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )
    slot_no = models.CharField(
        blank=True,
        help_text=_('Fill it if asset is blade server'),
        max_length=3,
        null=True,
        validators=[
            RegexValidator(
                regex=VALID_SLOT_NUMBER_FORMAT,
                message=_(
                    "Slot number should be a number from range 1-16 with "
                    "an optional postfix 'A' or 'B' (e.g. '16A')"
                ),
                code='invalid_slot_no'
            )
        ],
        verbose_name=_('slot number'),
    )
    connections = models.ManyToManyField(
        'self',
        through='Connection',
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
        'rack',
        'barcode',
        'sn',
    ]
    _summary_fields = [
        ('hostname', 'Hostname'),
        ('location', 'Location'),
        ('model__name', 'Model'),
    ]

    class Meta:
        verbose_name = _('data center asset')
        verbose_name_plural = _('data center assets')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Saved current rack value to check if changed.
        self._rack_id = self.rack_id

    def __str__(self):
        return '{} (BC: {} / SN: {})'.format(
            self.hostname or '-', self.barcode or '-', self.sn or '-'
        )

    def __repr__(self):
        return '<DataCenterAsset: {}>'.format(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # When changing rack we search and save all descendants
        if self.pk and self._rack_id != self.rack_id:
            DataCenterAsset.objects.filter(parent=self).update(rack=self.rack)

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

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

    def _get_management_ip(self):
        eth = self.ethernet.select_related('ipaddress').filter(
            ipaddress__is_management=True
        ).first()
        if eth:
            return eth.ipaddress
        return None

    @property
    def management_ip(self):
        ip = self._get_management_ip()
        if ip:
            return ip.address
        return ''

    @management_ip.setter
    def management_ip(self, value):
        ip = self._get_management_ip()
        if ip is None:
            return
        if ip:
            ip.address = value
            ip.save()
        else:
            IPAddress.objects.create(
                address=value,
                is_management=True,
            )

    @property
    def ipaddresses(self):
        return IPAddress.objects.filter(ethernet__base_object=self)

    @property
    def management_hostname(self):
        ip = self._get_management_ip()
        if ip:
            return ip.hostname
        return ''

    @management_hostname.setter
    def management_hostname(self, value):
        ip = self._get_management_ip()
        if ip is None:
            return
        if ip:
            ip.hostname = value
            ip.save()
        else:
            IPAddress.objects.create(
                hostname=value,
                is_management=True,
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
            * return first founded network environment if there is any,
              otherwise return `None`
        """
        if self.rack_id:
            return NetworkEnvironment.objects.filter(
                network__racks=self.rack
            ).distinct().first()

    @cached_property
    def location(self):
        """
        Additional column 'location' display filter by:
        data center, server_room, rack, position (if is blade)
        """
        base_url = reverse('admin:data_center_datacenterasset_changelist')
        position = self.position
        if self.is_blade:
            position = generate_html_link(
                base_url,
                {
                    'rack': self.rack_id,
                    'position__start': self.position,
                    'position__end': self.position
                },
                position,
            )

        result = [
            generate_html_link(
                base_url,
                {
                    'rack__server_room__data_center':
                        self.rack.server_room.data_center_id
                },
                self.rack.server_room.data_center.name
            ),
            generate_html_link(
                base_url,
                {'rack__server_room': self.rack.server_room_id},
                self.rack.server_room.name
            ),
            generate_html_link(
                base_url,
                {'rack': self.rack_id},
                self.rack.name
            )
        ] if self.rack else []

        if self.position:
            result.append(str(position))
        if self.slot_no:
            result.append(str(self.slot_no))

        return '&nbsp;/&nbsp;'.join(result) if self.rack else '&mdash;'

    def _get_available_network_environments(self):
        return list(NetworkEnvironment.objects.filter(
            network__racks=self.rack_id
        ).distinct())

    def _get_available_networks(self):
        return list(Network.objects.filter(
            racks=self.rack_id
        ).distinct())

    def _validate_orientation(self):
        """
        Validate if orientation is valid for given position.
        """
        if self.position is None:
            return
        if self.position == 0 and not Orientation.is_width(self.orientation):
            msg = 'Valid orientations for picked position are: {}'.format(
                ', '.join(
                    choice.desc for choice in Orientation.WIDTH.choices
                )
            )
            raise ValidationError({'orientation': [msg]})
        if self.position > 0 and not Orientation.is_depth(self.orientation):
            msg = 'Valid orientations for picked position are: {}'.format(
                ', '.join(
                    choice.desc for choice in Orientation.DEPTH.choices
                )
            )
            raise ValidationError({'orientation': [msg]})

    def _validate_position(self):
        """
        Validate if position not empty when rack requires it.
        """
        if (
            self.rack and
            self.position is None and
            self.rack.require_position
        ):
            msg = 'Position is required for this rack'
            raise ValidationError({'position': [msg]})

    def _validate_position_in_rack(self):
        """
        Validate if position is in rack height range.
        """
        if (
            self.rack and
            self.position is not None and
            self.position > self.rack.max_u_height
        ):
            msg = 'Position is higher than "max u height" = {}'.format(
                self.rack.max_u_height,
            )
            raise ValidationError({'position': [msg]})
        if self.position is not None and self.position < 0:
            msg = 'Position should be 0 or greater'
            raise ValidationError({'position': msg})

    def _validate_slot_no(self):
        if self.model_id:
            if self.model.has_parent and not self.slot_no:
                raise ValidationError({
                    'slot_no': 'Slot number is required when asset is blade'
                })
            if not self.model.has_parent and self.slot_no:
                raise ValidationError({
                    'slot_no': (
                        'Slot number cannot be filled when asset is not blade'
                    )
                })

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
            self._validate_slot_no
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
            assets_by_orientation.append(list(
                DataCenterAsset.objects.select_related('model').filter(
                    parent=self,
                    orientation=orientation,
                    model__has_parent=True,
                ).exclude(id=self.id)
            ))
        assets = [
            Gap.generate_gaps(assets) for assets in assets_by_orientation
        ]
        return chain(*assets)

    def get_next_free_hostname(self):
        """
        Returns next free hostname for this asset based on Rack's network
        environment (hostnaming template).
        """
        if self.network_environment:
            return self.network_environment.next_free_hostname
        logger.warning('Network-environment not provided for {}'.format(self))
        return ''

    def issue_next_free_hostname(self):
        """
        Reserve next (currently) free hostname and return it. You should assign
        this hostname to asset manually (or do with it whatever you like).
        """
        if self.network_environment:
            return self.network_environment.issue_next_free_hostname()
        logger.warning('Network-environment not provided for {}'.format(self))
        return ''

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(
            status=DataCenterAssetStatus.liquidated.id
        )

    @classmethod
    @transition_action(
        verbose_name=_('Change rack'),
        form_fields={
            'rack': {
                'field': forms.CharField(widget=AutocompleteWidget(
                    field=rack, admin_site=ralph_site
                )),
            }
        }
    )
    def change_rack(cls, instances, request, **kwargs):
        rack = Rack.objects.get(pk=kwargs['rack'])
        for instance in instances:
            instance.rack = rack

    @classmethod
    @transition_action(
        verbose_name=_('Convert to BackOffice Asset'),
        disable_save_object=True,
        only_one_action=True,
        form_fields={
            'warehouse': {
                'field': forms.CharField(label=_('Warehouse')),
                'autocomplete_field': 'warehouse',
                'autocomplete_model': 'back_office.BackOfficeAsset'
            },
            'region': {
                'field': forms.CharField(label=_('Region')),
                'autocomplete_field': 'region',
                'autocomplete_model': 'back_office.BackOfficeAsset'
            }
        }
    )
    def convert_to_backoffice_asset(cls, instances, request, **kwargs):
        with transaction.atomic():
            for i, instance in enumerate(instances):
                back_office_asset = BackOfficeAsset()

                back_office_asset.region = Region.objects.get(
                    pk=kwargs['region']
                )
                back_office_asset.warehouse = Warehouse.objects.get(
                    pk=kwargs['warehouse']
                )
                move_parents_models(instance, back_office_asset)
                # Save new asset to list, required to redirect url.
                # RunTransitionView.get_success_url()
                instances[i] = back_office_asset


class Connection(models.Model):
    outbound = models.ForeignKey(
        'DataCenterAsset',
        verbose_name=_('connected to device'),
        on_delete=models.PROTECT,
        related_name='outbound_connections',
    )
    inbound = models.ForeignKey(
        'DataCenterAsset',
        verbose_name=_('connected device'),
        on_delete=models.PROTECT,
        related_name='inbound_connections',
    )
    # TODO: discuss
    connection_type = models.PositiveIntegerField(
        verbose_name=_('connection type'),
        choices=ConnectionType()
    )

    def __str__(self):
        return '%s -> %s (%s)' % (
            self.outbound,
            self.inbound,
            self.connection_type
        )
