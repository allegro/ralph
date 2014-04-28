#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Component models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from decimal import Decimal

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    MACAddressField,
    Named,
    SavePrioritized,
    TimeTrackable,
    WithConcurrentGetOrCreate,
)
from lck.django.choices import Choices
from django.utils.html import escape

from ralph.discovery.models_util import SavingUser


MAC_PREFIX_BLACKLIST = set([
    '505054', '33506F', '009876', '000000', '00000C', '204153', '149120',
    '020054', 'FEFFFF', '1AF920', '020820', 'DEAD2C', 'FEAD4D',
])
CPU_CORES = {
    '5160': 2,
    'E5320': 4,
    'E5430': 4,
    'E5504': 4,
    'E5506': 4,
    'E5520': 4,
    'E5540': 4,
    'E5630': 4,
    'E5620': 4,
    'E5640': 4,
    'E5645': 6,
    'E5649': 6,
    'L5520': 4,
    'L5530': 4,
    'L5420': 4,
    'L5630': 4,
    'X5460': 4,
    'X5560': 4,
    'X5570': 4,
    'X5650': 6,
    'X5660': 6,
    'X5670': 6,
    'E5-2640': 6,
    'E5-2670': 8,
    'E5-2630': 6,
    'E5-2650': 8,
    'E7-8837': 8,
    'E7- 8837': 8,
    'E7-4870': 10,
    'E7- 4870': 10,
    'Processor 275': 2,
    'Processor 8216': 2,
    'Processor 6276': 16,
    'Dual-Core': 2,
    'Quad-Core': 4,
    'Six-Core': 6,
    '2-core': 2,
    '4-core': 4,
    '6-core': 6,
    '8-core': 8,
}
CPU_VIRTUAL_LIST = {
    'bochs',
    'qemu',
    'virtual',
    'vmware',
    'xen',
}


def cores_from_model(model_name):
    for name, cores in CPU_CORES.iteritems():
        if name in model_name:
            return cores
    return 0


def is_mac_valid(eth):
    try:
        mac = MACAddressField.normalize(eth.mac)
        if not mac:
            return False
        for black in MAC_PREFIX_BLACKLIST:
            if mac.startswith(black):
                return False
        return True
    except ValueError:
        return False


def is_virtual_cpu(family):
    family = family.lower()
    return any(virtual in family for virtual in CPU_VIRTUAL_LIST)


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
    price = db.PositiveIntegerField(
        verbose_name=_("purchase price"),
        null=True,
        blank=True,
    )
    type = db.PositiveIntegerField(
        verbose_name=_("component type"),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    per_size = db.BooleanField(
        default=False,
        verbose_name=_("This price is per unit of size"),
    )
    size_unit = db.CharField(
        verbose_name=_("unit of size"),
        blank=True,
        default="",
        max_length=50,
    )
    size_modifier = db.PositiveIntegerField(
        verbose_name=_("size modifier"),
        default=1,
    )

    class Meta:
        verbose_name = _("group of component models")
        verbose_name_plural = _("groups of component models")

    def get_count(self):
        return sum(
            model.objects.filter(model__group=self).count()
            for model in (
                Storage, Memory, Processor, DiskShare, FibreChannel,
                GenericComponent, Software,
            )
        )


class ComponentModel(SavePrioritized, WithConcurrentGetOrCreate, SavingUser):
    name = db.CharField(verbose_name=_("name"), max_length=255)
    speed = db.PositiveIntegerField(
        verbose_name=_("speed (MHz)"),
        default=0,
        blank=True,
    )
    cores = db.PositiveIntegerField(
        verbose_name=_("number of cores"),
        default=0,
        blank=True,
    )
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"),
        default=0,
        blank=True,
    )
    type = db.PositiveIntegerField(
        verbose_name=_("component type"),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    group = db.ForeignKey(
        ComponentModelGroup,
        verbose_name=_("group"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    family = db.CharField(blank=True, default='', max_length=128)

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family')
        verbose_name = _("component model")
        verbose_name_plural = _("component models")

    def __unicode__(self):
        return self.name

    @classmethod
    def concurrent_get_or_create(cls, *args, **kwargs):
        raise AssertionError(
            "Direct usage of this method on ComponentModel is forbidden."
        )

    @classmethod
    def create(cls, type, priority, **kwargs):
        """More robust API for concurrent_get_or_create. All arguments should
        be given flat.

        Required arguments: type; priority; family (for processors and disks)

        Forbidden arguments: name (for memory and disks)

        All other arguments are optional and sensible defaults are given. For
        each ComponentModel type a minimal sensible set of arguments should be
        given.

        name is truncated to 50 characters.
        """

        # sanitize None, 0 and empty strings
        kwargs = {
            name: kwargs[name]
            for name in ('speed', 'cores', 'size', 'family', 'group', 'name')
            if name in kwargs and kwargs[name]
        }
        # put sensible empty values
        kwargs.setdefault('speed', 0)
        kwargs.setdefault('cores', 0)
        kwargs.setdefault('size', 0)
        kwargs['type'] = type or ComponentType.unknown
        family = kwargs.setdefault('family', '')
        group = kwargs.pop('group', None)
        if kwargs['type'] == ComponentType.memory:
            assert 'name' not in kwargs, "Custom `name` forbidden for memory."
            name = ' '.join(['RAM', family])
            if kwargs['size']:
                name += ' %dMiB' % int(kwargs['size'])
            if kwargs['speed']:
                name += ', %dMHz' % int(kwargs['speed'])
        elif kwargs['type'] == ComponentType.disk:
            assert 'name' not in kwargs, "Custom `name` forbidden for disks."
            assert family, "`family` not given (required for disks)."
            name = family
            if kwargs['size']:
                name += ' %dMiB' % int(kwargs['size'])
            if kwargs['speed']:
                name += ', %dRPM' % int(kwargs['speed'])
        else:
            name = kwargs.pop('name', family)
        kwargs.update({
            'group': group,
            'name': name[:50],
        })
        if kwargs['type'] == ComponentType.processor:
            assert family, "`family` not given (required for CPUs)."
            kwargs['cores'] = max(
                1,
                kwargs['cores'],
                cores_from_model(name) if not is_virtual_cpu(family) else 1,
            )
            kwargs['size'] = kwargs['cores']
        try:
            unique_args = {
                name: kwargs[name]
                for name in ('speed', 'cores', 'size', 'type', 'family')
            }
            obj = cls.objects.get(**unique_args)
            return obj, False
        except cls.DoesNotExist:
            obj = cls(**kwargs)
            obj.save(priority=priority)
            return obj, True

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
            'count': self.get_count()
        }

    def is_software(self):
        return True if self.type == ComponentType.software else False


class Component(SavePrioritized, WithConcurrentGetOrCreate):
    device = db.ForeignKey('Device', verbose_name=_("device"))
    model = db.ForeignKey(
        ComponentModel,
        verbose_name=_("model"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )

    class Meta:
        abstract = True

    def get_price_formula(self, date=None):
        """
        Find a custom formula for this component's price for specified date.
        """
        if not (self.model and self.model.group):
            return None
        if date is None:
            date = datetime.date.today()
        month = datetime.date(date.year, date.month, 1)
        for formula in self.model.group.pricingformula_set.filter(
            group__date=month,
            group__devices=self.device,
        ):
            return formula
        return None

    def get_price(self):
        if not self.model:
            return 0
        return self.model.get_price(self.get_size())

    def get_size(self):
        if self.model and self.model.size:
            return self.model.size
        return getattr(self, 'size', 0) or 0


class GenericComponent(Component):
    label = db.CharField(
        verbose_name=_("name"), max_length=255, blank=True,
        null=True, default=None,
    )
    sn = db.CharField(
        verbose_name=_("vendor SN"), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )
    boot_firmware = db.CharField(
        verbose_name=_("boot firmware"), null=True, blank=True, max_length=255,
    )
    hard_firmware = db.CharField(
        verbose_name=_("hardware firmware"), null=True, blank=True,
        max_length=255,
    )
    diag_firmware = db.CharField(
        verbose_name=_("diagnostics firmware"), null=True, blank=True,
        max_length=255,
    )
    mgmt_firmware = db.CharField(
        verbose_name=_("management firmware"), null=True, blank=True,
        max_length=255,
    )

    class Meta:
        verbose_name = _("generic component")
        verbose_name_plural = _("generic components")

    def __unicode__(self):
        if self.model:
            return "{} ({}): {} {}".format(
                self.label, self.sn, self.model, self.model.get_type_display(),
            )
        return "{} ({})".format(self.label, self.sn)


class DiskShare(Component):
    share_id = db.PositiveIntegerField(
        verbose_name=_("share identifier"), null=True, blank=True,
    )
    label = db.CharField(
        verbose_name=_("name"), max_length=255, blank=True, null=True,
        default=None,
    )
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )
    snapshot_size = db.PositiveIntegerField(
        verbose_name=_("size for snapshots (MiB)"), null=True, blank=True,
    )
    wwn = db.CharField(
        verbose_name=_("Volume serial"), max_length=33, unique=True,
    )
    full = db.BooleanField(default=True)

    class Meta:
        verbose_name = _("disk share")
        verbose_name_plural = _("disk shares")

    def __unicode__(self):
        return '%s (%s)' % (self.label, self.wwn)

    def get_total_size(self):
        return (self.size or 0) + (self.snapshot_size or 0)

    def get_price(self):
        """
        Return the price of the disk share. This is calculated as for all
        other components, unless the share is in a currently active pricing
        group -- then the formula for that particular component from that
        pricing group is used. In case the formula is invalid in some way
        for the specified values (for example, it has division by zero),
        NaN is returned instead of a price.
        """
        if self.device and self.device.is_deprecated():
            return 0
        if not (self.model and self.model.group):
            return 0
        size = self.get_total_size() / 1024
        formula = self.get_price_formula()
        if formula:
            try:
                return float(formula.get_value(size=Decimal(size)))
            except Exception:
                return float('NaN')
        return (self.model.group.price or 0) * size


class DiskShareMount(TimeTrackable, WithConcurrentGetOrCreate):
    share = db.ForeignKey(DiskShare, verbose_name=_("share"))
    device = db.ForeignKey('Device', verbose_name=_("device"), null=True,
                           blank=True, default=None, on_delete=db.SET_NULL)
    volume = db.CharField(verbose_name=_("volume"),
                          max_length=255, blank=True,
                          null=True, default=None)
    server = db.ForeignKey(
        'Device', verbose_name=_("server"), null=True, blank=True,
        default=None, related_name='servermount_set',
    )
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )
    address = db.ForeignKey("IPAddress", null=True, blank=True, default=None)
    is_virtual = db.BooleanField(
        verbose_name=_("is that a virtual server mount?"), default=False,
    )

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
        if self.share.device and self.share.device.is_deprecated():
            return 0
        if self.size and self.share.model and self.share.model.group:
            size = self.get_size() / 1024
            formula = self.share.get_price_formula()
            if formula:
                try:
                    return float(formula.get_value(size=Decimal(size)))
                except Exception:
                    return float('NaN')
            return (self.share.model.group.price or 0) * size
        return self.share.get_price() / (self.get_total_mounts() or 1)


class Processor(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    speed = db.PositiveIntegerField(
        verbose_name=_("speed (MHz)"), null=True, blank=True,
    )
    cores = db.PositiveIntegerField(
        verbose_name=_("number of cores"), null=True, blank=True,
    )
    index = db.PositiveIntegerField(
        verbose_name=_("slot number"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _("processor")
        verbose_name_plural = _("processors")
        ordering = ('device', 'index')
        unique_together = ('device', 'index')

    def __init__(self, *args, **kwargs):
        super(Processor, self).__init__(*args, **kwargs)
        self.cores = self.guess_core_count()

    def __unicode__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)

    def get_cores(self):
        if self.model and self.model.cores:
            return self.model.cores
        return self.cores or 1

    def guess_core_count(self):
        """Guess the number of cores for a CPU model."""
        if self.model:
            return max(
                1,
                self.model.cores,
                self.cores,
                self.model.size,
                cores_from_model(
                    self.model.name
                ) if not is_virtual_cpu(self.model.name) else 1,
            )
        return max(1, self.cores)

    def save(self, *args, **kwargs):
        if self.model:
            self.cores = self.model.cores
        return super(Processor, self).save(*args, **kwargs)

    @property
    def size(self):
        return self.get_cores()


class Memory(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )
    speed = db.PositiveIntegerField(
        verbose_name=_("speed (MHz)"), null=True, blank=True,
    )
    index = db.PositiveIntegerField(
        verbose_name=_("slot number"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _("memory")
        verbose_name_plural = _("memories")
        ordering = ('device', 'index')
        unique_together = ('device', 'index')

    def __unicode__(self):
        return '#{}: {} ({})'.format(self.index, self.label, self.model)


class Storage(Component):
    sn = db.CharField(
        verbose_name=_("vendor SN"), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )
    label = db.CharField(verbose_name=_("name"), max_length=255)
    mount_point = db.CharField(
        verbose_name=_("mount point"), max_length=255, null=True, blank=True,
        default=None,
    )
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )

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
    speed = db.PositiveIntegerField(
        verbose_name=_("speed"), choices=EthernetSpeed(),
        default=EthernetSpeed.unknown.id,
    )

    class Meta:
        verbose_name = _("ethernet")
        verbose_name_plural = _("ethernets")
        ordering = ('device', 'mac')

    def __unicode__(self):
        return '{} ({})'.format(self.label, self.mac)


class Software(Component):
    sn = db.CharField(
        verbose_name=_("vendor SN"), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )
    label = db.CharField(verbose_name=_("name"), max_length=255)
    # bash and widnows have a limit on the path length
    path = db.CharField(
        verbose_name=_("path"), max_length=255, null=True, blank=True,
        default=None,
    )
    version = db.CharField(verbose_name=_("version"), max_length=255,
                           null=True, blank=True, default=None)

    class Meta:
        verbose_name = _("software")
        verbose_name_plural = _("software")
        ordering = ('device', 'sn', 'path')
        unique_together = ('device', 'path')

    def __unicode__(self):
        return '%r' % self.label

    @classmethod
    def create(cls, dev, path, model_name, priority, label=None, sn=None,
               family=None, version=None):
        model, created = ComponentModel.create(
            ComponentType.software,
            family=family,
            name=model_name,
            priority=priority,
        )
        software, created = cls.concurrent_get_or_create(
            device=dev,
            path=path,
            defaults={
                'model': model,
                'label': label or model_name,
                'sn': sn,
                'version': version,
            }
        )
        if created:
            software.mark_dirty(
                'device',
                'path',
                'model',
                'label',
                'sn',
                'version',
            )
            software.save(priority=priority)
        # FIXME: should model, label, sn and version be updated for
        #        existing objects?
        return software


class SplunkUsage(Component):
    day = db.DateField(verbose_name=_("day"), auto_now_add=True)
    size = db.PositiveIntegerField(
        verbose_name=_("size (MiB)"), null=True, blank=True,
    )

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

    @classmethod
    def get_cost(cls, venture, start, end, shallow=False):
        splunk_usage = cls.objects.filter(day__gte=start, day__lte=end)
        if venture and venture != '*':
            if shallow:
                splunk_usage = splunk_usage.filter(device__venture=venture)
            else:
                splunk_usage = splunk_usage.filter(
                    db.Q(device__venture=venture) |
                    db.Q(device__venture__parent=venture) |
                    db.Q(device__venture__parent__parent=venture) |
                    db.Q(device__venture__parent__parent__parent=venture) |
                    db.Q(
                        device__venture__parent__parent__parent__parent=venture
                    )
                )
        elif not venture:  # specifically "devices with no venture set"
            splunk_usage = splunk_usage.filter(device__venture=None)
        if splunk_usage.count():
            splunk_size = splunk_usage.aggregate(
                db.Sum('size')
            )['size__sum'] or 0
            splunk_count = splunk_usage.values('device').distinct().count()
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            splunk_count_now = SplunkUsage.objects.filter(
                day=yesterday,
            ).values('device').distinct().count()
            splunk_cost = splunk_usage[0].get_price(size=splunk_size)
            return splunk_cost, splunk_count, splunk_count_now, splunk_size
        return None, None, None, None


class OperatingSystem(Component):
    label = db.CharField(verbose_name=_("name"), max_length=255)
    memory = db.PositiveIntegerField(
        verbose_name=_("memory"), help_text=_("in MiB"), null=True, blank=True,
    )
    storage = db.PositiveIntegerField(
        verbose_name=_("storage"), help_text=_("in MiB"), null=True,
        blank=True,
    )
    cores_count = db.PositiveIntegerField(
        verbose_name=_("cores count"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _("operating system")
        verbose_name_plural = _("operating systems")
        ordering = ('label',)
        unique_together = ('device',)

    def __unicode__(self):
        return self.label

    @classmethod
    def create(cls, dev, os_name, priority, version='', memory=None,
               storage=None, cores_count=None, family=None):
        model, created = ComponentModel.create(
            ComponentType.os,
            family=family,
            name=os_name,
            priority=priority,
        )
        operating_system, created = cls.concurrent_get_or_create(
            device=dev,
            defaults={
                'model': model,
            }
        )
        operating_system.label = '%s %s' % (os_name, version)
        operating_system.memory = memory
        operating_system.storage = storage
        operating_system.cores_count = cores_count
        operating_system.save(priority=priority)
        return operating_system
