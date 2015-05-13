# -*- coding: utf-8 -*-

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import (
    Asset,
    BasePhysicalAsset,
    NamedMixin
)
from ralph.data_center.models.choices import (
    Orientation,
    RackOrientation,
    ConnectionType
)


@python_2_unicode_compatible
class DataCenter(NamedMixin, models.Model):

    visualization_cols_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid columns number'),
        default=20,
    )
    visualization_rows_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid rows number'),
        default=20,
    )

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ServerRoom(NamedMixin.NonUnique, models.Model):
    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))

    def __str__(self):
        return '{} ({})'.format(self.name, self.data_center.name)


class Accessory(NamedMixin):

    class Meta:
        verbose_name = _('accessory')
        verbose_name_plural = _('accessories')


@python_2_unicode_compatible
class RackAccessory(models.Model):
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
    class Meta:
        unique_together = ('name', 'server_room')

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


class DataCenterAsset(BasePhysicalAsset, Asset):

    rack = models.ForeignKey(Rack)

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

    @property
    def cores_count(self):
        """Returns cores count assigned to device in Ralph"""
        asset_cores_count = self.model.cores_count if self.model else 0
        return asset_cores_count

    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=False,
    )

    class Meta:
        verbose_name = _('data center asset')
        verbose_name_plural = _('data center assets')


@python_2_unicode_compatible
class Connection(models.Model):

    outbound = models.ForeignKey(
        'DataCenterAsset',
        verbose_name=_("connected to device"),
        on_delete=models.PROTECT,
        related_name='outbound_connections',
    )
    inbound = models.ForeignKey(
        'DataCenterAsset',
        verbose_name=_("connected device"),
        on_delete=models.PROTECT,
        related_name='inbound_connections',
    )
    # TODO: discuss
    connection_type = models.PositiveIntegerField(
        verbose_name=_("connection type"),
        choices=ConnectionType()
    )

    def __str__(self):
        return "%s -> %s (%s)" % (
            self.outbound,
            self.inbound,
            self.connection_type
        )
