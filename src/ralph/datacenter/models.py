# -*- coding: utf-8 -*-

from dj.choices import Choices

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import (
    Asset,
    BasePhysicalAsset,
    Component,
    NamedMixin
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


class Orientation(Choices):
    _ = Choices.Choice

    DEPTH = Choices.Group(0)
    front = _("front")
    back = _("back")
    middle = _("middle")

    WIDTH = Choices.Group(100)
    left = _("left")
    right = _("right")

    @classmethod
    def is_width(cls, orientation):
        is_width = orientation in set(
            [choice.id for choice in cls.WIDTH.choices]
        )
        return is_width

    @classmethod
    def is_depth(cls, orientation):
        is_depth = orientation in set(
            [choice.id for choice in cls.DEPTH.choices]
        )
        return is_depth


class RackOrientation(Choices):
    _ = Choices.Choice

    top = _("top")
    bottom = _("bottom")
    left = _("left")
    right = _("right")


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
        verbose_name = _('DC Asset')
        verbose_name_plural = _('DC Assets')


class Database(Asset):
    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')


class VIP(Asset):
    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')


class VirtualServer(Asset):
    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')


class CloudProject(Asset):
    pass


# TODO: discuss
class ConnectionType(Choices):
    _ = Choices.Choice

    network = _("network connection")


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


@python_2_unicode_compatible
class DiskShare(Component):
    share_id = models.PositiveIntegerField(
        verbose_name=_('share identifier'), null=True, blank=True,
    )
    label = models.CharField(
        verbose_name=_('name'), max_length=255, blank=True, null=True,
        default=None,
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'), null=True, blank=True,
    )
    snapshot_size = models.PositiveIntegerField(
        verbose_name=_('size for snapshots (MiB)'), null=True, blank=True,
    )
    wwn = models.CharField(
        verbose_name=_('Volume serial'), max_length=33, unique=True,
    )
    full = models.BooleanField(default=True)

    def get_total_size(self):
        return (self.size or 0) + (self.snapshot_size or 0)

    class Meta:
        verbose_name = _('disk share')
        verbose_name_plural = _('disk shares')

    def __str__(self):
        return '%s (%s)' % (self.label, self.wwn)


@python_2_unicode_compatible
class DiskShareMount(models.Model):
    share = models.ForeignKey(DiskShare, verbose_name=_("share"))
    asset = models.ForeignKey(
        Asset, verbose_name=_('asset'), null=True, blank=True,
        default=None, on_delete=models.SET_NULL
    )
    volume = models.CharField(
        verbose_name=_('volume'), max_length=255, blank=True,
        null=True, default=None
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'), null=True, blank=True,
    )

    def get_total_mounts(self):
        return self.share.disksharemount_set.exclude(
            device=None
        ).filter(
            is_virtual=False
        ).count()

    def get_size(self):
        return self.size or self.share.get_total_size()

    class Meta:
        unique_together = ('share', 'asset')
        verbose_name = _('disk share mount')
        verbose_name_plural = _('disk share mounts')

    def __str__(self):
        return '%s@%r' % (self.volume, self.asset)
