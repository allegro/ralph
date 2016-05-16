# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.assets.models.assets import Asset
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ComponentType
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin


class ComponentModel(AutocompleteTooltipMixin, NamedMixin, models.Model):
    speed = models.PositiveIntegerField(
        verbose_name=_('speed (MHz)'),
        default=0,
        blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name=_('number of cores'),
        default=0,
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'),
        default=0,
        blank=True,
    )
    type = models.PositiveIntegerField(
        verbose_name=_('component type'),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    family = models.CharField(blank=True, default='', max_length=128)

    autocomplete_tooltip_fields = [
        'speed',
        'cores',
        'size',
        'type',
        'family',
    ]

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family')
        verbose_name = _('component model')
        verbose_name_plural = _('component models')

    def __str__(self):
        return self.name


class Component(models.Model):
    base_object = models.ForeignKey(BaseObject, related_name='%(class)s')
    model = models.ForeignKey(
        ComponentModel,
        verbose_name=_('model'),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True


class GenericComponent(Component):
    label = models.CharField(
        verbose_name=_('label'), max_length=255, blank=True,
        null=True, default=None,
    )
    sn = NullableCharField(
        verbose_name=_('vendor SN'), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )

    class Meta:
        verbose_name = _('generic component')
        verbose_name_plural = _('generic components')


class DiskShareComponent(Component):
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
    wwn = NullableCharField(
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


class DiskShareMountComponent(models.Model):
    share = models.ForeignKey(DiskShareComponent, verbose_name=_('share'))
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

    def get_size(self):
        return self.size or self.share.get_total_size()

    class Meta:
        unique_together = ('share', 'asset')
        verbose_name = _('disk share mount')
        verbose_name_plural = _('disk share mounts')

    def __str__(self):
        return '%s@%r' % (self.volume, self.asset)


class ProcessorComponent(Component):

    label = models.CharField(verbose_name=_('name'), max_length=255)
    speed = models.PositiveIntegerField(
        verbose_name=_('speed (MHz)'), null=True, blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name=_('number of cores'), null=True, blank=True,
    )
    index = models.PositiveIntegerField(
        verbose_name=_('slot number'), null=True, blank=True,
    )

    class Meta:
        verbose_name = _('processor')
        verbose_name_plural = _('processors')

    def __str__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)

    def get_cores(self):
        if self.model and self.model.cores:
            return self.model.cores
        return self.cores or 1

    def save(self, *args, **kwargs):
        if self.model:
            self.cores = self.model.cores
        return super().save(*args, **kwargs)


class MemoryComponent(Component):
    label = models.CharField(verbose_name=_('name'), max_length=255)
    size = models.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )
    speed = models.PositiveIntegerField(
        verbose_name=_("speed (MHz)"), null=True, blank=True,
    )
    index = models.PositiveIntegerField(
        verbose_name=_("slot number"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _('memory')
        verbose_name_plural = _('memories')

    def __str__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)


class FibreChannelComponent(Component):
    physical_id = models.CharField(verbose_name=_('name'), max_length=32)
    label = models.CharField(verbose_name=_('name'), max_length=255)

    class Meta:
        verbose_name = _('fibre channel')
        verbose_name_plural = _('fibre channels')

    def __str__(self):
        return '{} ({})'.format(self.label, self.physical_id)


class SoftwareComponent(Component):
    sn = models.CharField(
        verbose_name=_('vendor SN'), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )
    label = models.CharField(verbose_name=_('name'), max_length=255)
    # bash and windows have a limit on the path length
    path = models.CharField(
        verbose_name=_('path'), max_length=255, null=True, blank=True,
        default=None,
    )
    version = models.CharField(
        verbose_name=_('version'), max_length=255, null=True, blank=True,
        default=None
    )

    class Meta:
        verbose_name = _('software')
        verbose_name_plural = _('software')

    def __str__(self):
        return '%r' % self.label


class OperatingSystemComponent(Component):
    label = models.CharField(verbose_name=_('name'), max_length=255)
    memory = models.PositiveIntegerField(
        verbose_name=_('memory'), help_text=_('in MiB'), null=True, blank=True,
    )
    storage = models.PositiveIntegerField(
        verbose_name=_('storage'), help_text=_('in MiB'), null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('operating system')
        verbose_name_plural = _('operating systems')

    def __str__(self):
        return self.label
