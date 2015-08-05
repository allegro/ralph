# -*- coding: utf-8 -*-
import re
from collections import namedtuple
from itertools import chain

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import AdminAbsoluteUrlMixin, Asset, NamedMixin
from ralph.assets.models.choices import AssetSource
from ralph.data_center.models.choices import (
    ConnectionType,
    Orientation,
    RackOrientation
)

# i.e. number in range 1-16 and optional postfix 'A' or 'B'
VALID_SLOT_NUMBER_FORMAT = re.compile('^([1-9][A,B]?|1[0-6][A,B]?)$')


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


class DataCenter(NamedMixin, models.Model):

    visualization_cols_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid columns number'),
        default=20,
    )
    visualization_rows_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid rows number'),
        default=20,
    )

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
    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))

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
        return 'RackAccessory: {rack_name} - {accessory_name}'.format(
            rack_name=rack_name, accessory_name=accessory_name,
        )


class Rack(NamedMixin.NonUnique, models.Model):

    server_room = models.ForeignKey(
        ServerRoom, verbose_name=_('server room'),
        null=True,
        blank=True,
    )
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

    class Meta:
        unique_together = ('name', 'server_room')

    def __str__(self):
        return "{} ({}/{})".format(
            self.name,
            self.server_room.data_center,
            self.server_room.name,
        )

    def get_orientation_desc(self):
        return RackOrientation.name_from_id(self.orientation)

    def get_root_assets(self, side=None):
        filter_kwargs = {
            'rack': self,
            'slot_no': '',
        }
        if side:
            filter_kwargs['orientation'] = side
        return DataCenterAsset.objects.select_related(
            'model', 'model__category'
        ).filter(**filter_kwargs).exclude(model__has_parent=True)

    def get_free_u(self):
        dc_assets = self.get_root_assets()
        dc_assets_height = dc_assets.aggregate(
            sum=models.Sum('model__height_of_device'))['sum'] or 0
        # accesory always has 1U of height
        accessories = RackAccessory.objects.values_list(
            'position', flat=True).filter(rack=self)
        return self.max_u_height - dc_assets_height - len(set(accessories))

    def get_pdus(self):
        return DataCenterAsset.objects.select_related('model').filter(
            rack=self,
            orientation__in=(Orientation.left, Orientation.right),
            position=0,
        )


class DataCenterAsset(Asset):

    rack = models.ForeignKey(Rack, null=True)
    position = models.IntegerField(null=True)
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

    # TODO: convert to foreign key
    configuration_path = models.CharField(
        help_text=_('Path to configuration for e.g. puppet, chef.'),
        max_length=100,
        verbose_name=_('configuration path'),
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

    class Meta:
        verbose_name = _('data center asset')
        verbose_name_plural = _('data center assets')

    def __str__(self):
        return '{} <id: {}>'.format(self.hostname, self.id)

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

    @property
    def cores_count(self):
        """Returns cores count assigned to device in Ralph"""
        asset_cores_count = self.model.cores_count if self.model else 0
        return asset_cores_count

    @property
    def management_ip(self):
        """A property that gets management IP of a asset."""
        management_ip = self.ipaddress_set.filter(is_management=True).order_by(
            '-address'
        ).first()
        return management_ip.address if management_ip else ''

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

    def clean(self):
        # TODO: this should be default logic of clean method;
        # we could register somehow validators (or take each func with
        # _validate prefix) and call it here
        errors = {}
        for validator in [
            super().clean,
            self._validate_orientation,
            self._validate_position_in_rack
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
