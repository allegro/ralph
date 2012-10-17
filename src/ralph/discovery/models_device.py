#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Device models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import re

from django.db import models as db
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (Named, WithConcurrentGetOrCreate,
        MACAddressField, SavePrioritized, SoftDeletable, TimeTrackable)
from lck.django.choices import Choices
from lck.django.common import nested_commit_on_success
from lck.django.tags.models import Taggable
from django.utils.html import escape

from ralph.discovery.models_component import is_mac_valid, Ethernet
from ralph.discovery.models_util import LastSeen, SavingUser
from ralph.util import Eth


BLADE_SERVERS = [
    r'^IBM (eServer )?BladeCenter',
    r'^HP ProLiant BL',
]

BLADE_SERVERS_RE = re.compile('|'.join(('(%s)' % r) for r in BLADE_SERVERS))

SERIAL_BLACKLIST = set([
    None, '', 'Not Available', 'XxXxXxX', '-----', '[Unknown]', '0000000000',
    'Not Specified', 'YK10CD', '1234567890', 'None', 'To Be Filled By O.E.M.',
])

DISK_VENDOR_BLACKLIST = set(['lsi', 'lsilogic', 'vmware', '3pardata'])
DISK_PRODUCT_BLACKLIST = set(['mr9261-8i', '9750-4i', 'msa2324fc',
    'logical volume', 'virtualdisk', 'virtual-disk', 'multi-flex',
    '1815      fastt', 'comstar'])


class DeviceType(Choices):
    _ = Choices.Choice

    INFRASTRUCTURE = Choices.Group(0)
    rack = _("rack")
    blade_system = _("blade system")
    management = _("management")
    power_distribution_unit = _("power distribution unit")
    data_center = _("data center")

    NETWORK_EQUIPMENT = Choices.Group(100)
    switch = _("switch")
    router = _("router")
    load_balancer = _("load balancer")
    firewall = _("firewall")
    smtp_gateway = _("SMTP gateway")
    appliance = _("Appliance")

    SERVERS = Choices.Group(200)
    rack_server = _("rack server")
    blade_server = _("blade server") << { 'matches': BLADE_SERVERS_RE.match }
    virtual_server = _("virtual server")
    cloud_server = _("cloud server")

    STORAGE = Choices.Group(300)
    storage = _("storage")
    fibre_channel_switch = _("fibre channel switch")

    UNKNOWN = Choices.Group(400)
    unknown = _("unknown")


class DeprecationKind(TimeTrackable, Named):
    months = db.PositiveIntegerField(verbose_name=_("deprecation time in months"),
        blank=True, null=True)
    remarks = db.TextField(verbose_name=_("remarks"),
        help_text=_("additional information."),
        blank=True, default="")
    default = db.BooleanField(default=False)

    class Meta:
        verbose_name = _("deprecation kind")
        verbose_name_plural = _("deprecation kinds")

    def save(self, *args, **kwargs):
        if self.dirty_fields.get('months') is not None:
            devices = Device.objects.filter(deprecation_kind_id = self.id)
            for device in devices:
                if (device.purchase_date is not None
                    and device.deprecation_kind_id is not None):
                    device.deprecation_date = (device.purchase_date +
                                               relativedelta(months=self.months))
                    super(Device, device).save(*args, **kwargs)
        return super(DeprecationKind, self).save(*args, **kwargs)


class MarginKind(Named):
    margin = db.PositiveIntegerField(verbose_name=_("margin in percents"),
        blank=True, null=True)
    remarks = db.TextField(verbose_name=_("remarks"),
        help_text=_("additional information."),
        blank=True, default="")

    class Meta:
        verbose_name = _("margin kind")
        verbose_name_plural = _("margin kinds")


class DeviceModelGroup(Named, TimeTrackable, SavingUser):
    price = db.PositiveIntegerField(verbose_name=_("purchase price"),
        null=True, blank=True)
    type = db.PositiveIntegerField(verbose_name=_("device type"),
        choices=DeviceType(), default=DeviceType.unknown.id)
    slots = db.FloatField(verbose_name=_("number of slots"), default=0)

    class Meta:
        verbose_name = _("group of device models")
        verbose_name_plural = _("groups of device models")

    def get_count(self):
        return Device.objects.filter(model__group=self).count()


class DeviceModel(SavePrioritized, WithConcurrentGetOrCreate, SavingUser):
    name = db.CharField(verbose_name=_("name"), max_length=255, unique=True)
    type = db.PositiveIntegerField(verbose_name=_("device type"),
        choices=DeviceType(), default=DeviceType.unknown.id)
    group = db.ForeignKey(DeviceModelGroup, verbose_name=_("group"),
        null=True, blank=True, default=None, on_delete=db.SET_NULL)
    chassis_size = db.PositiveIntegerField(
            verbose_name=_("chassis size"), null=True, blank=True)


    class Meta:
        verbose_name = _("device model")
        verbose_name_plural = _("device models")

    def __unicode__(self):
        return "[{}] {}".format(self.get_type_display(), self.name)

    def get_count(self):
        return self.device_set.count()

    def get_price(self):
        if self.group:
            return self.group.price
        return 0

    def get_json(self):
        return {
            'id': 'D%d' % self.id,
            'name': escape(self.name or ''),
            'count': self.device_set.count(),
        }


class UptimeSupport(db.Model):
    """Adds an `uptime` attribute to the model. This attribute is shifted
    by the current time on each get. Returns a timedelta object, accepts
    None, timedelta and int values on set."""
    uptime_seconds = db.PositiveIntegerField(
        verbose_name=_("uptime in seconds"), default=0)
    uptime_timestamp = db.DateTimeField(verbose_name=_("uptime timestamp"),
        null=True, blank=True, help_text=_("moment of the last uptime update"))

    class Meta:
        abstract = True

    @property
    def uptime(self):
        if not self.uptime_seconds or not self.uptime_timestamp:
            return None
        return datetime.now() - self.uptime_timestamp + \
            timedelta(seconds=self.uptime_seconds)

    @uptime.setter
    def uptime(self, value):
        if not value:
            del self.uptime
            return
        if isinstance(value, timedelta):
            value = abs(int(value.total_seconds()))
        self.uptime_seconds = value
        self.uptime_timestamp = datetime.now()

    @uptime.deleter
    def uptime(self):
        self.uptime_seconds = 0
        self.uptime_timestamp = None

    def get_uptime_display(self):
        u = self.uptime
        if not u:
            return _("unknown")
        if u.days == 1:
            msg = _("1 day")
        else:
            msg = _("%d days") % u.days
        hours = int(u.seconds / 60 / 60)
        minutes = int(u.seconds / 60) - 60 * hours
        seconds = int(u.seconds) - 3600 * hours - 60 * minutes
        return msg + ", %02d:%02d:%02d" % (hours, minutes, seconds)


class Device(LastSeen, Taggable.NoDefaultTags, SavePrioritized,
    WithConcurrentGetOrCreate, UptimeSupport, SoftDeletable, SavingUser):
    name = db.CharField(verbose_name=_("name"), max_length=255)
    name2 = db.CharField(verbose_name=_("extra name"), max_length=255,
        null=True, blank=True, default=None)
    parent = db.ForeignKey('self', verbose_name=_("parent device"),
        on_delete=db.SET_NULL,
        null=True, blank=True, default=None, related_name="child_set")
    model = db.ForeignKey(DeviceModel, verbose_name=_("model"), null=True,
        blank=True, default=None, related_name="device_set",
        on_delete=db.SET_NULL)
    sn = db.CharField(verbose_name=_("serial number"), max_length=255,
        unique=True, null=True, blank=True, default=None)
    barcode = db.CharField(verbose_name=_("barcode"), max_length=255,
        unique=True, null=True, blank=True, default=None)
    remarks = db.TextField(verbose_name=_("remarks"),
        help_text=_("Additional information."),
        blank=True, default="")
    raw = db.TextField(verbose_name=_("raw info"),
        help_text=_("Response information as received."),
        blank=True, default=None, null=True, editable=False)
    boot_firmware = db.CharField(verbose_name=_("boot firmware"), null=True,
            blank=True, max_length=255)
    hard_firmware = db.CharField(verbose_name=_("hardware firmware"),
            null=True, blank=True, max_length=255)
    diag_firmware = db.CharField(verbose_name=_("diagnostics firmware"),
            null=True, blank=True, max_length=255)
    mgmt_firmware = db.CharField(verbose_name=_("management firmware"),
            null=True, blank=True, max_length=255)
    price = db.PositiveIntegerField(verbose_name=_("manual price"),
        null=True, blank=True)
    purchase_date = db.DateTimeField(verbose_name=_("purchase date"),
        null=True, blank=True)
    deprecation_date = db.DateTimeField(verbose_name=_("deprecation date"),
        null=True, blank=True)
    cached_price = db.FloatField(verbose_name=_("quoted price"),
        null=True, blank=True)
    cached_cost = db.FloatField(verbose_name=_("monthly cost"),
        null=True, blank=True)
    warranty_expiration_date = db.DateTimeField(
        verbose_name=_("warranty expiration"), null=True, blank=True)
    support_expiration_date = db.DateTimeField(
        verbose_name=_("support expiration"), null=True, blank=True)
    support_kind = db.CharField(verbose_name=_("support kind"),
            null=True, blank=True, max_length=255)
    deprecation_kind = db.ForeignKey(DeprecationKind,
        verbose_name=_("deprecation"), on_delete=db.SET_NULL,
        null=True, blank=True, default=None)
    margin_kind = db.ForeignKey(MarginKind, verbose_name=_("margin"),
        null=True, blank=True, default=None, on_delete=db.SET_NULL)
    chassis_position = db.PositiveIntegerField(
            verbose_name=_("numeric position"), null=True, blank=True)
    position = db.CharField(verbose_name=_("position"),
            null=True, blank=True, max_length=16)
    venture = db.ForeignKey("business.Venture", verbose_name=_("venture"),
                            null=True, blank=True, default=None,
                            on_delete=db.SET_NULL)
    management = db.ForeignKey("IPAddress", related_name="managed_set",
                            verbose_name=_("management address"),
                            null=True, blank=True, default=None,
                            on_delete=db.SET_NULL)
    role = db.CharField(verbose_name=_("old role"), null=True, blank=True,
                        max_length=255)
    venture_role = db.ForeignKey("business.VentureRole", on_delete=db.SET_NULL,
        verbose_name=_("role"), null=True, blank=True, default=None)
    dc = db.CharField(verbose_name=_("data center"), max_length=32,
        null=True, blank=True, default=None)
    rack = db.CharField(verbose_name=_("rack"), max_length=32,
        null=True, blank=True, default=None)
    verified = db.BooleanField(verbose_name=_("verified"), default=False)

    class Meta:
        verbose_name = _("device")
        verbose_name_plural = _("devices")

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.being_deleted = False
        self.saving_user = None
        super(Device, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.id)

    @classmethod
    def create(cls, ethernets=None, sn=None, model=None,  model_name=None,
               model_type=None, device=None, allow_stub=False, priority=0,
               **kwargs):
        if 'parent' in kwargs and kwargs['parent'] is None:
            del kwargs['parent']
        if not model and (not model_name or not model_type):
            raise ValueError(
                    'Either provide model or model_type and model_name.')
        dev = device
        ethernets = [Eth(*e) for e in (ethernets or []) if
                     is_mac_valid(Eth(*e))]
        if ethernets:
            macs = set([MACAddressField.normalize(eth.mac) for
                        eth in ethernets])
            devs = Device.admin_objects.filter(
                        ethernet__mac__in=macs).distinct()
            if len(devs) > 1:
                raise ValueError('Multiple devices match MACs: %r' % macs)
            elif len(devs) == 1:
                if dev and devs[0].id != dev.id:
                    raise ValueError('Conflict of devices %r and %r!' % (
                        dev, devs[0]))
                else:
                    dev = devs[0]
        if sn:
            sn = sn.strip()
        if sn in SERIAL_BLACKLIST:
            sn = None
        if not any((sn, ethernets, allow_stub)):
            raise ValueError("Neither `sn` nor `ethernets` given. "
                "Use `allow_stub` to override.")
        if sn:
            try:
                sndev = Device.admin_objects.get(sn=sn)
            except Device.DoesNotExist:
                pass
            else:
                if dev is None:
                    dev = sndev
                elif sndev.id != dev.id:
                    if any((# both devices are properly placed in the tree
                            sndev.parent and dev.parent,
                            # the device found using ethernets (or explicitly
                            # given as `device`) has different sn than `sn`
                            dev.sn and dev.sn != sn,
                            # the device found using `sn` already has other
                            # ethernets
                            sndev.ethernet_set.exists())):
                        raise ValueError('Conflict of devices %r and %r!' %
                                (dev, sndev))
                    sndev.delete()
        if model is None:
            model, model_created = DeviceModel.concurrent_get_or_create(
                name=model_name, type=model_type.id)
        if dev is None:
            dev, created = Device.concurrent_get_or_create(sn=sn, model=model)
        elif dev.deleted:
            dev.deleted = False
        if model and model.type != DeviceType.unknown.id:
            dev.model = model
        if not dev.sn and sn:
            dev.sn = sn
        for k, v in kwargs.iteritems():
            if k in ('name', 'last_seen'):
                continue
            setattr(dev, k, v)
        dev.save(update_last_seen=True, priority=priority)

        for eth in ethernets:
            ethernet, eth_created = Ethernet.concurrent_get_or_create(
                    device=dev, mac=eth.mac)
            if eth_created:
                ethernet.label = eth.label or 'Autocreated'
                if eth.speed:
                    ethernet.speed = eth.speed
            ethernet.save(priority=priority)
        return dev

    def get_margin(self):
        if self.margin_kind:
            return self.margin_kind.margin
        elif self.venture:
            return self.venture.get_margin()
        return 0


    @classmethod
    @nested_commit_on_success
    def get_or_create_by_mac(cls, mac, **kwargs):
        mac = MACAddressField.normalize(mac)
        try:
            obj = Ethernet.objects.get(mac=mac).device
            created = False
        except Ethernet.DoesNotExist:
            try:
                obj = cls.objects.create(**kwargs)
                created = True
            except IntegrityError, e1:
                transaction.commit()
                try:
                    obj = cls.objects.filter(ethernet__mac=mac).get(**kwargs)
                except cls.DoesNotExist, e2:
                    raise e1 # there is an object with a partial argument match
                created = False
            else:
                eth = Ethernet.objects.create(device=obj, mac=mac,
                        label='Autocreated')
        return obj, created

    def get_name(self):
        dev = self
        if dev.model and dev.model.type in (DeviceType.rack.id,
                                            DeviceType.data_center.id):
            return dev.name
        for ipaddr in dev.ipaddress_set.exclude(hostname=None).order_by(
                'is_management', '-last_seen', '-address'):
            return ipaddr.hostname
        for ipaddr in dev.ipaddress_set.order_by(
                'is_management', '-last_seen', '-address'):
            return ipaddr.hostname or ipaddr.address
        return 'unknown'


    def find_management(self):
        for ipaddr in self.ipaddress_set.filter(is_management=True).order_by('-address'):
            return ipaddr
        if self.management:
            return self.management
        return None

    def get_model_name(self):
        try:
            return self.model.group.name
        except AttributeError:
            return self.model.name if self.model else ''

    def get_position(self):
        if self.position:
            return self.position
        if self.chassis_position is None:
            return ''
        if self.chassis_position > 2000:
            pos = '%dB' % (self.chassis_position - 2000)
        elif self.chassis_position > 1000:
            pos = '%dA' % (self.chassis_position - 1000)
        else:
            pos = '%d' % self.chassis_position
        return pos

    def get_last_ping(self):
        for ip in self.ipaddress_set.order_by('-last_seen'):
            return ip.last_seen

    def get_deprecation_kind(self):
        if self.deprecation_kind:
            return self.deprecation_kind
        try:
            default_deprecation_kind = DeprecationKind.objects.get(default=True)
        except DeprecationKind.DoesNotExist:
            return None
        else:
            return default_deprecation_kind

    @property
    def ipaddress(self):
        return self.ipaddress_set

    @property
    def rolepropertyvalue(self):
        return self.rolepropertyvalue_set

    def save(self, *args, **kwargs):
        if self.model.type == DeviceType.blade_server.id:
            if not self.position:
                self.position = self.get_position()
        if self.purchase_date and self.deprecation_kind:
            self.deprecation_date = (self.purchase_date +
                           relativedelta(months = self.deprecation_kind.months))
        return super(Device, self).save(*args, **kwargs)


class ReadOnlyDevice(Device):
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        assert False, "Cannot save read only models."

    def _fields_as_dict(self):
        return {}


class LoadBalancerPool(Named, WithConcurrentGetOrCreate):
    class Meta:
        verbose_name = _("load balancer pool")
        verbose_name_plural = _("load balancer pools")


class LoadBalancerVirtualServer(SavePrioritized, WithConcurrentGetOrCreate):
    name = db.CharField(verbose_name=_("name"), max_length=255)
    device = db.ForeignKey(Device, verbose_name=_("load balancer device"))
    default_pool = db.ForeignKey(LoadBalancerPool)
    address = db.ForeignKey("IPAddress", verbose_name=_("address"))
    port = db.PositiveIntegerField(verbose_name=_("port"))

    class Meta:
        verbose_name = _("load balancer virtual server")
        verbose_name_plural = _("load balancer virtual servers")

    def __unicode__(self):
        return "{} ({})".format(self.name, self.id)


class LoadBalancerMember(SavePrioritized, WithConcurrentGetOrCreate):
    address = db.ForeignKey("IPAddress", verbose_name=_("address"))
    port = db.PositiveIntegerField(verbose_name=_("port"))
    pool = db.ForeignKey(LoadBalancerPool)
    device = db.ForeignKey(Device, verbose_name=_("load balancer device"))
    enabled = db.BooleanField(verbose_name=_("enabled state"))

    class Meta:
        verbose_name = _("load balancer pool membership")
        verbose_name_plural = _("load balancer pool memberships")
        unique_together = ('pool', 'address', 'port', 'device')

    def __unicode__(self):
        return "{}:{}@{}({})".format(self.address.address, self.port,
                self.pool.name, self.id)


class Warning(db.Model, WithConcurrentGetOrCreate):
    category = db.CharField(verbose_name=_("category"), max_length=128)
    address = db.ForeignKey('IPAddress', verbose_name=_("address"),
            related_name='warning_set', null=True)
    device = db.ForeignKey(Device, verbose_name=_("device"),
            related_name='warning_set', null=True)
    remarks = db.TextField(verbose_name=_("remarks"), blank=True, default="")
    aknowledged = db.CharField(verbose_name=_("acknowledged"),
            max_length=128, default="", blank=True)

    class Meta:
        verbose_name = _("warning")
        verbose_name_plural = _("warnings")
        unique_together = ('category', 'address', 'device')

