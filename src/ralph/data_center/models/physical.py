# -*- coding: utf-8 -*-
import re
from collections import namedtuple
from itertools import chain

from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import (
    AdminAbsoluteUrlMixin,
    Asset,
    NamedMixin,
)
from ralph.data_center.models.choices import (
    ConnectionType,
    Orientation,
    RackOrientation,
)


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

    # TODO: maybe move to objectModel?
    slots = models.FloatField(
        verbose_name='Slots',
        help_text=('For blade centers: the number of slots available in this '
                   'device. For blade devices: the number of slots occupied.'),
        max_length=64,
        default=0,
    )
    slot_no = models.CharField(
        verbose_name=_('slot number'), max_length=3, null=True, blank=True,
        help_text=_('Fill it if asset is blade server'),
    )
    # TODO: convert to foreign key
    configuration_path = models.CharField(
        _('configuration path'),
        max_length=100,
        help_text=_('Path to configuration for e.g. puppet, chef.'),
    )
    position = models.IntegerField(null=True)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )

    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=False,
    )

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

    @property
    def management_ip(self):
        """A property that gets management IP of a asset."""
        management_ip = self.ipaddress_set.filter(is_management=True).order_by(
            '-address'
        ).first()
        return management_ip.address if management_ip else ''


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
