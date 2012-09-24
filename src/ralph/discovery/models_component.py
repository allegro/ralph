#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Component models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (TimeTrackable, Named,
    WithConcurrentGetOrCreate, MACAddressField, SavePrioritized)
from lck.django.choices import Choices
from django.utils.html import escape

from ralph.discovery.models_util import SavingUser


MAC_PREFIX_BLACKLIST = set([
    '505054', '33506F', '009876', '000000', '00000C', '204153', '149120',
    '020054', 'FEFFFF', '1AF920', '020820', 'DEAD2C', 'FEAD4D',
])

def is_mac_valid(eth):
    try:
        mac = MACAddressField.normalize(eth.mac)
        for black in MAC_PREFIX_BLACKLIST:
            if mac.startswith(black):
                return False
        return True
    except ValueError:
        return False


class EthernetSpeed(Choices):
    _ = Choices.Choice

    s10mbit = _("10 Mbps")
    s100mbit = _("100 Mbps")
    s1gbit = _("1 Gbps")
    s10gbit = _("10 Gbps")

    UNKNOWN_GROUP = Choices.Group(10)
    unknown = _("unknown speed")


class ComponentType(Choices):
    _ = Choices.Choice

    processor = _("processor")
    memory = _("memory")
    disk = _("disk drive")
    ethernet = _("ethernet card")
    expansion = _("expansion card")
    fibre = _("fibre channel card")
    share = _("disk share")
    unknown = _("unknown")
    management = _("management")
    power = _("power module")
    cooling = _("cooling device")
    media = _("media tray")
    chassis = _("chassis")
    backup = _("backup")
    software = _("software")
    os = _('operating system')


class ComponentModelGroup(Named, TimeTrackable, SavingUser):
    price = db.PositiveIntegerField(verbose_name=_("purchase price"),
        null=True, blank=True)
    type = db.PositiveIntegerField(verbose_name=_("component type"),
        choices=ComponentType(), default=ComponentType.unknown.id)
    per_size = db.BooleanField(default=False,
            verbose_name=_("This price is per unit of size"))
    size_unit = db.CharField(verbose_name=_("unit of size"), blank=True,
        default="", max_length=50)
    size_modifier = db.PositiveIntegerField(verbose_name=_("size modifier"),
        default=1)

    class Meta:
        verbose_name = _("group of component models")
        verbose_name_plural = _("groups of component models")

    def get_count(self):
        return sum(model.objects.filter(model__group=self).count()
            for model in (Storage, Memory, Processor, DiskShare, FibreChannel,
                GenericComponent, Software))


class ComponentModel(Named.NonUnique, SavePrioritized,
                     WithConcurrentGetOrCreate, SavingUser):
    speed = db.PositiveIntegerField(verbose_name=_("speed (MHz)"),
        default=0, blank=True)
    cores = db.PositiveIntegerField(verbose_name=_("number of cores"),
        default=0, blank=True)
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        default=0, blank=True)
    type = db.PositiveIntegerField(verbose_name=_("component type"),
        choices=ComponentType(), default=ComponentType.unknown.id)
    group = db.ForeignKey(ComponentModelGroup, verbose_name=_("group"),
        null=True, blank=True, default=None, on_delete=db.SET_NULL)
    extra = db.TextField(verbose_name=_("additional information"),
        help_text=_("Additional information."), blank=True, default=None, null=True)
    extra_hash = db.CharField(blank=True, default='', max_length=32)
    family = db.CharField(blank=True, default='', max_length=128)

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family', 'extra_hash')
        verbose_name = _("component model")
        verbose_name_plural = _("component models")

    def get_price(self, size=None):
        if not self.group:
            return 0
        if self.group.per_size:
            if not size:
                size = self.size
            return (size /
                    (self.group.size_modifier or 1)) * (self.group.price or 0)
        else:
            return self.group.price or 0

    def get_count(self):
        return sum([
                self.storage_set.count(),
                self.memory_set.count(),
                self.processor_set.count(),
                self.diskshare_set.count(),
                self.fibrechannel_set.count(),
                self.genericcomponent_set.count(),
                self.software_set.count(),
                self.operatingsystem_set.count(),
            ])

    def get_json(self):
        return {
            'id': 'C%d' % self.id,
            'name': escape(self.name or ''),
            'family': escape(self.family or ''),
            'speed': self.speed,
            'size': self.size,
            'cores': self.cores,
            'extra': escape(self.extra or ''),
            'count': self.get_count()
        }


class Component(SavePrioritized, WithConcurrentGetOrCreate):
    device = db.ForeignKey('Device', verbose_name=_("device"))
    model = db.ForeignKey(ComponentModel, verbose_name=_("model"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL)

    class Meta:
        abstract = True

    def get_price(self):
        if not self.model:
            return 0
        return self.model.get_price(getattr(self, 'size', 0) or 0)


class GenericComponent(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255, blank=True,
                         null=True, default=None)
    sn = db.CharField(verbose_name=_("vendor SN"), max_length=255,
        unique=True, null=True, blank=True, default=None)
    boot_firmware = db.CharField(verbose_name=_("boot firmware"), null=True,
            blank=True, max_length=255)
    hard_firmware = db.CharField(verbose_name=_("hardware firmware"),
            null=True, blank=True, max_length=255)
    diag_firmware = db.CharField(verbose_name=_("diagnostics firmware"),
            null=True, blank=True, max_length=255)
    mgmt_firmware = db.CharField(verbose_name=_("management firmware"),
            null=True, blank=True, max_length=255)

    class Meta:
        verbose_name = _("generic component")
        verbose_name_plural = _("generic components")

    def __unicode__(self):
        return "{} ({}): {} {}".format(self.label, self.sn,
            self.model, self.model.get_type_display())


class DiskShare(Component):
    share_id = db.PositiveIntegerField(verbose_name=_("share identifier"),
        null=True, blank=True)
    label = db.CharField(verbose_name=_("name"), max_length=255, blank=True,
                         null=True, default=None)
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        null=True, blank=True)
    snapshot_size = db.PositiveIntegerField(
        verbose_name=_("size for snapshots (MiB)"), null=True, blank=True)
    wwn = db.CharField(verbose_name=_("Volume serial"), max_length=33, unique=True)
    full = db.BooleanField(default=True)

    class Meta:
        verbose_name = _("disk share")
        verbose_name_plural = _("disk shares")

    def __unicode__(self):
        return '%s (%s)' % (self.label, self.wwn)

    def get_total_size(self):
        return (self.size or 0) + (self.snapshot_size or 0)

    def get_price(self):
        if self.model and self.model.group:
            return (self.model.group.price or 0) * self.get_total_size() / 1024
        return 0

class DiskShareMount(TimeTrackable, WithConcurrentGetOrCreate):
    share = db.ForeignKey(DiskShare, verbose_name=_("share"))
    device = db.ForeignKey('Device', verbose_name=_("device"), null=True,
                           blank=True, default=None, on_delete=db.SET_NULL)
    volume = db.CharField(verbose_name=_("volume"),
                          max_length=255, blank=True,
                          null=True, default=None)
    server = db.ForeignKey('Device', verbose_name=_("server"),
        null=True, blank=True, default=None, related_name='servermount_set')
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        null=True, blank=True)
    address = db.ForeignKey("IPAddress", null=True, blank=True, default=None)
    is_virtual = db.BooleanField(verbose_name=_("is that a virtual server mount?"),
            default=False)

    class Meta:
        unique_together = ('share', 'device')
        verbose_name = _("disk share mount")
        verbose_name_plural = _("disk share mounts")

    def __unicode__(self):
        return '%s@%r' % (self.volume, self.device)

    def get_total_mounts(self):
        return self.share.disksharemount_set.exclude(
                device=None
            ).filter(
                is_virtual=False
            ).count()

    def get_size(self):
        return self.size or self.share.get_total_size()

    def get_price(self):
        if self.size and self.share.model and self.share.model.group:
            return (self.share.model.group.price or 0) * self.get_size() / 1024
        return self.share.get_price() / (self.get_total_mounts() or 1)


class Processor(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    speed = db.PositiveIntegerField(verbose_name=_("speed (MHz)"),
        null=True, blank=True)
    cores = db.PositiveIntegerField(verbose_name=_("number of cores"),
        null=True, blank=True)
    index = db.PositiveIntegerField(verbose_name=_("slot number"),
        null=True, blank=True)

    class Meta:
        verbose_name = _("processor")
        verbose_name_plural = _("processors")
        ordering = ('device', 'index')
        unique_together = ('device', 'index')

    def __unicode__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)


class Memory(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        null=True, blank=True)
    speed = db.PositiveIntegerField(verbose_name=_("speed (MHz)"),
        null=True, blank=True)
    index = db.PositiveIntegerField(verbose_name=_("slot number"),
        null=True, blank=True)

    class Meta:
        verbose_name = _("memory")
        verbose_name_plural = _("memories")
        ordering = ('device', 'index')
        unique_together = ('device', 'index')

    def __unicode__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)


class Storage(Component):
    sn = db.CharField(verbose_name=_("vendor SN"), max_length=255,
        unique=True, null=True, blank=True, default=None)
    label = db.CharField(verbose_name=_("name"), max_length=255)
    mount_point = db.CharField(verbose_name=_("mount point"), max_length=255,
        null=True, blank=True, default=None)
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        null=True, blank=True)

    class Meta:
        verbose_name = _("storage")
        verbose_name_plural = _("storages")
        ordering = ('device', 'sn', 'mount_point')
        unique_together = ('device', 'mount_point')

    def __unicode__(self):
        if not self.mount_point:
            return '{} ({})'.format(self.label, self.model)
        return '{} at {} ({})'.format(self.label, self.mount_point, self.model)

    def get_size(self):
        if self.model and self.model.size:
            return self.model.size
        return self.size or 0


class FibreChannel(Component):
    physical_id = db.CharField(verbose_name=_("name"), max_length=32)
    label = db.CharField(verbose_name=_("name"), max_length=255)

    class Meta:
        verbose_name = _("fibre channel")
        verbose_name_plural = _("fibre channels")
        ordering = ('device', 'physical_id')
        unique_together = ('device', 'physical_id')

    def __unicode__(self):
        return '{} ({})'.format(self.label, self.physical_id)


class Ethernet(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    mac = MACAddressField(verbose_name=_("MAC address"), unique=True)
    speed = db.PositiveIntegerField(verbose_name=_("speed"),
        choices=EthernetSpeed(), default=EthernetSpeed.unknown.id)

    class Meta:
        verbose_name = _("ethernet")
        verbose_name_plural = _("ethernets")
        ordering = ('device', 'mac')

    def __unicode__(self):
        return '{} ({})'.format(self.label, self.mac)


class Software(Component):
    sn = db.CharField(verbose_name=_("vendor SN"), max_length=255,
        unique=True, null=True, blank=True, default=None)
    label = db.CharField(verbose_name=_("name"), max_length=255)
    # bash and widnows have a limit on the path length
    path = db.CharField(verbose_name=_("path"), max_length=255,
        null=True, blank=True, default=None)

    @classmethod
    def create(cls, dev, path, model_name, label=None, sn=None, family=None):
        model, created = ComponentModel.concurrent_get_or_create(
                type=ComponentType.software.id,
                family=family,
                extra_hash=hashlib.md5(model_name.encode('utf-8', 'replace')).hexdigest(),
            )
        if created:
            model.extra = model_name
            model.name = model_name
            model.save()
        software, created = cls.concurrent_get_or_create(device=dev, path=path)
        software.model = model
        software.label = label or model_name
        software.sn = sn
        return software

    class Meta:
        verbose_name = _("software")
        verbose_name_plural = _("software")
        ordering = ('device', 'sn', 'path')
        unique_together = ('device', 'path')

    def __unicode__(self):
        return '%r at %r (%r)' % (self.label, self.path, self.model)


class SplunkUsage(Component):
    day = db.DateField(verbose_name=_("day"), auto_now_add=True)
    size = db.PositiveIntegerField(verbose_name=_("size (MiB)"),
        null=True, blank=True)

    class Meta:
        verbose_name = _("Splunk usage")
        verbose_name_plural = _("Splunk usages")
        ordering = ('device', 'day')
        unique_together = ('device', 'day')

    def __unicode__(self):
        return '#{}: {}'.format(self.day, self.model)

    def get_price(self, size=None):
        if not self.model:
            return 0
        if not size:
            size = self.size
        return self.model.get_price(size=size)


class OperatingSystem(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    memory = db.PositiveIntegerField(verbose_name=_("memory"),
        help_text=_("in MiB"), null=True, blank=True)
    storage = db.PositiveIntegerField(verbose_name=_("storage"),
        help_text=_("in MiB"), null=True, blank=True)
    cores_count = db.PositiveIntegerField(verbose_name=_("cores count"),
        null=True, blank=True)

    @classmethod
    def create(cls, dev, os_name, version='', memory=None, storage=None,
               cores_count=None, family=None):
        model, created = ComponentModel.concurrent_get_or_create(
            type=ComponentType.os.id,
            family=family,
            extra_hash=hashlib.md5(os_name.encode('utf-8', 'replace')).hexdigest()
        )
        if created:
            model.name = os_name
            model.save()
        try:
            operating_system = cls.objects.get(device=dev)
        except cls.DoesNotExist:
            operating_system = cls.objects.create(device=dev)
        operating_system.model = model
        operating_system.label = '%s %s' % (os_name, version)
        operating_system.memory = memory
        operating_system.storage = storage
        operating_system.cores_count = cores_count
        return operating_system

    class Meta:
        verbose_name = _("operating system")
        verbose_name_plural = _("operating systems")
        ordering = ('label',)

    def __unicode__(self):
        return self.label
