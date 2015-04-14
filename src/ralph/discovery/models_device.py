#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Device models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta
import datetime
import re
import sys
import os
from collections import Iterable

from django.conf import settings
from django.contrib.contenttypes.generic import GenericRelation
from django.core.urlresolvers import reverse
from django.db import models as db
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    MACAddressField,
    Named,
    SavePrioritized,
    SoftDeletable,
    TimeTrackable,
    WithConcurrentGetOrCreate,
)
from lck.django.choices import Choices
from lck.django.common import nested_commit_on_success
from lck.django.tags.models import Taggable
from django.utils.html import escape

from ralph.cmdb import models_ci
from ralph.discovery.models_component import is_mac_valid, Ethernet
from ralph.discovery.models_network import IPAddress
from ralph.discovery.models_util import LastSeen, SavingUser
from ralph.util import Eth
from ralph.util.models import SyncFieldMixin


BLADE_SERVERS = [
    r'^IBM (eServer )?BladeCenter',
    r'^HP ProLiant BL',
]


BLADE_SERVERS_RE = re.compile('|'.join(('(%s)' % r) for r in BLADE_SERVERS))


SERIAL_BLACKLIST = set([
    None, '', 'Not Available', 'XxXxXxX', '-----', '[Unknown]', '0000000000',
    'Not Specified', 'YK10CD', '1234567890', 'None', 'To Be Filled By O.E.M.',
])

DISK_VENDOR_BLACKLIST = set([
    'lsi', 'lsilogic', 'vmware', '3pardata',
])


DISK_PRODUCT_BLACKLIST = set([
    'mr9261-8i', '9750-4i', 'msa2324fc',
    'logical volume', 'virtualdisk', 'virtual-disk', 'multi-flex',
    '1815      fastt', 'comstar',
])

SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE = getattr(
    settings, 'SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE', False
)


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
    switch_stack = _("switch stack")

    SERVERS = Choices.Group(200)
    rack_server = _("rack server")
    blade_server = _("blade server") << {'matches': BLADE_SERVERS_RE.match}
    virtual_server = _("virtual server")
    cloud_server = _("cloud server")

    STORAGE = Choices.Group(300)
    storage = _("storage")
    fibre_channel_switch = _("fibre channel switch")
    mogilefs_storage = _("MogileFS storage")

    UNKNOWN = Choices.Group(400)
    unknown = _("unknown")


class ConnectionType(Choices):
    _ = Choices.Choice

    network = _("network connection")


class DeprecationKind(TimeTrackable, Named):
    months = db.PositiveIntegerField(
        verbose_name=_("deprecation time in months"),
        blank=True,
        null=True,
    )
    remarks = db.TextField(
        verbose_name=_("remarks"),
        help_text=_("additional information."),
        blank=True,
        default="",
    )
    default = db.BooleanField(default=False)

    class Meta:
        verbose_name = _("deprecation kind")
        verbose_name_plural = _("deprecation kinds")

    def save(self, *args, **kwargs):
        if self.dirty_fields.get('months') is not None:
            devices = Device.objects.filter(deprecation_kind_id=self.id)
            for device in devices:
                if (
                    device.purchase_date is not None and
                    device.deprecation_kind_id is not None
                ):
                    device.deprecation_date = (
                        device.purchase_date +
                        relativedelta(months=self.months)
                    )
                    super(Device, device).save(*args, **kwargs)
        return super(DeprecationKind, self).save(*args, **kwargs)


class MarginKind(Named):
    margin = db.PositiveIntegerField(
        verbose_name=_("margin in percents"),
        blank=True,
        null=True,
    )
    remarks = db.TextField(
        verbose_name=_("remarks"),
        help_text=_("additional information."),
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("margin kind")
        verbose_name_plural = _("margin kinds")


class DeviceModel(SavePrioritized, WithConcurrentGetOrCreate, SavingUser):
    name = db.CharField(
        verbose_name=_("name"),
        max_length=255,
        unique=True,
    )
    type = db.PositiveIntegerField(
        verbose_name=_("device type"),
        choices=DeviceType(),
        default=DeviceType.unknown.id,
    )
    chassis_size = db.PositiveIntegerField(
        verbose_name=_("chassis size"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("device model")
        verbose_name_plural = _("device models")

    def __unicode__(self):
        return "[{}] {}".format(self.get_type_display(), self.name)

    def get_count(self):
        return self.device_set.count()

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
        verbose_name=_("uptime in seconds"),
        default=0,
    )
    uptime_timestamp = db.DateTimeField(
        verbose_name=_("uptime timestamp"),
        null=True,
        blank=True,
        help_text=_("moment of the last uptime update"),
    )

    class Meta:
        abstract = True

    @property
    def uptime(self):
        if not self.uptime_seconds or not self.uptime_timestamp:
            return None
        return (datetime.datetime.now() - self.uptime_timestamp +
                datetime.timedelta(seconds=self.uptime_seconds))

    @uptime.setter
    def uptime(self, value):
        if not value:
            del self.uptime
            return
        if isinstance(value, datetime.timedelta):
            value = abs(int(value.total_seconds()))
        self.uptime_seconds = value
        self.uptime_timestamp = datetime.datetime.now()

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
        return "%s, %02d:%02d:%02d" % (msg, hours, minutes, seconds)


class DeviceEnvironmentManager(db.Manager):
    def get_query_set(self):
        return super(DeviceEnvironmentManager, self).get_query_set().filter(
            type__name=models_ci.CI_TYPES.ENVIRONMENT,
            state=models_ci.CI_STATE_TYPES.ACTIVE,
        )


class DeviceEnvironment(models_ci.CI):
    """
    Catalog of environment where device is used, like: prod, test, ect.
    """
    objects = DeviceEnvironmentManager()

    class Meta:
        proxy = True

    def __unicode__(self):
        return self.name


class ServiceCatalogManager(db.Manager):
    def get_query_set(self):
        if SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE:
            ids = models_ci.CIAttributeValue.objects.filter(
                attribute__pk=7,
                value_boolean__value=True,
                ci__type=models_ci.CI_TYPES.SERVICE,
            ).values('ci')
            services = super(
                ServiceCatalogManager,
                self,
            ).get_query_set().filter(
                state=models_ci.CI_STATE_TYPES.ACTIVE,
                id__in=ids,
            )
        else:
            services = super(
                ServiceCatalogManager, self,
            ).get_query_set().filter(
                type=models_ci.CI_TYPES.SERVICE,
                state=models_ci.CI_STATE_TYPES.ACTIVE,
            )
        return services


class ServiceCatalog(models_ci.CI):
    """
    Catalog of services where device is used, like: allegro.pl
    """
    objects = ServiceCatalogManager()

    class Meta:
        proxy = True

    def __unicode__(self):
        return self.name

    def get_environments(self):
        env_ids_from_service = models_ci.CIRelation.objects.filter(
            parent=self.id,
        ).values('child__id')
        envs = DeviceEnvironment.objects.filter(id__in=env_ids_from_service)
        return envs


class Device(
    LastSeen,
    Taggable.NoDefaultTags,
    SavePrioritized,
    WithConcurrentGetOrCreate,
    UptimeSupport,
    SoftDeletable,
    SavingUser,
    SyncFieldMixin,
):
    name = db.CharField(
        verbose_name=_("name"),
        max_length=255
    )
    name2 = db.CharField(
        verbose_name=_("extra name"),
        max_length=255,
        null=True,
        blank=True,
        default=None,
    )
    parent = db.ForeignKey(
        'self',
        verbose_name=_("physical parent device"),
        on_delete=db.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="child_set",
    )
    logical_parent = db.ForeignKey(
        'self',
        verbose_name=_("logical parent device"),
        on_delete=db.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="logicalchild_set",
    )
    connections = db.ManyToManyField(
        'Device',
        through='Connection',
        symmetrical=False,
    )
    model = db.ForeignKey(
        DeviceModel,
        verbose_name=_("model"),
        null=True,
        blank=True,
        default=None,
        related_name="device_set",
        on_delete=db.SET_NULL,
    )
    sn = db.CharField(
        verbose_name=_("serial number"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )
    barcode = db.CharField(
        verbose_name=_("barcode"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )
    remarks = db.TextField(
        verbose_name=_("remarks"),
        help_text=_("Additional information."),
        blank=True,
        default="",
    )
    boot_firmware = db.CharField(
        verbose_name=_("boot firmware"),
        null=True,
        blank=True,
        max_length=255,
    )
    hard_firmware = db.CharField(
        verbose_name=_("hardware firmware"),
        null=True,
        blank=True,
        max_length=255,
    )
    diag_firmware = db.CharField(
        verbose_name=_("diagnostics firmware"),
        null=True,
        blank=True,
        max_length=255,
    )
    mgmt_firmware = db.CharField(
        verbose_name=_("management firmware"),
        null=True,
        blank=True,
        max_length=255,
    )
    price = db.PositiveIntegerField(
        verbose_name=_("manual price"),
        null=True,
        blank=True,
    )
    purchase_date = db.DateTimeField(
        verbose_name=_("purchase date"),
        null=True,
        blank=True,
    )
    deprecation_date = db.DateTimeField(
        verbose_name=_("deprecation date"),
        null=True,
        blank=True,
    )
    cached_price = db.FloatField(
        verbose_name=_("quoted price"),
        null=True,
        blank=True,
    )
    cached_cost = db.FloatField(
        verbose_name=_("monthly cost"),
        null=True,
        blank=True,
    )
    warranty_expiration_date = db.DateTimeField(
        verbose_name=_("warranty expiration"),
        null=True,
        blank=True,
    )
    support_expiration_date = db.DateTimeField(
        verbose_name=_("support expiration"),
        null=True,
        blank=True,
    )
    support_kind = db.CharField(
        verbose_name=_("support kind"),
        null=True,
        blank=True,
        default=None,
        max_length=255,
    )
    deprecation_kind = db.ForeignKey(
        DeprecationKind,
        verbose_name=_("deprecation"),
        on_delete=db.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )
    margin_kind = db.ForeignKey(
        MarginKind,
        verbose_name=_("margin"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    chassis_position = db.PositiveIntegerField(
        verbose_name=_("position (U level)"),
        null=True,
        blank=True,
    )
    position = db.CharField(
        verbose_name=_("slot no"),
        null=True,
        blank=True,
        max_length=16,
    )
    venture = db.ForeignKey(
        "business.Venture",
        verbose_name=_("venture"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    management = db.ForeignKey(
        "IPAddress",
        related_name="managed_set",
        verbose_name=_("management address"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    role = db.CharField(
        verbose_name=_("old role"),
        null=True,
        blank=True,
        max_length=255,
    )
    venture_role = db.ForeignKey(
        "business.VentureRole",
        on_delete=db.SET_NULL,
        verbose_name=_("role"),
        null=True,
        blank=True,
        default=None,
    )
    dc = db.CharField(
        verbose_name=_("data center"),
        max_length=32,
        null=True,
        blank=True,
        default=None
    )
    rack = db.CharField(
        verbose_name=_("rack"),
        max_length=32,
        null=True,
        blank=True,
        default=None,
    )
    verified = db.BooleanField(verbose_name=_("verified"), default=False)
    service = db.ForeignKey(
        ServiceCatalog,
        default=None,
        null=True,
        on_delete=db.PROTECT,
        related_name='device',
    )
    device_environment = db.ForeignKey(
        DeviceEnvironment,
        default=None,
        null=True,
        on_delete=db.PROTECT,
        related_name='device',
    )

    class Meta:
        verbose_name = _("device")
        verbose_name_plural = _("devices")

    if 'cmdb' in settings.PLUGGABLE_APPS:
        from ralph.cmdb.models_ci import CI
        ci_set = GenericRelation(CI)

        @property
        def ci(self):
            from ralph.cmdb.models_ci import CI
            try:
                return self.ci_set.get()
            except CI.DoesNotExist:
                return None

        @ci.setter
        def ci(self, value):
            from ralph.cmdb.models_ci import CI
            if self.ci_set.count():
                self.ci_set.all().delete()
            if value and isinstance(value, CI):
                self.ci_set.add(value)

    def clean(self):
        fields_list = [
            self.sn,
            self.support_kind,
            self.name2,
            self.dc,
            self.rack,
            self.role,
            self.position,
            self.mgmt_firmware,
            self.hard_firmware,
            self.diag_firmware,
            self.boot_firmware,
            self.barcode,
        ]
        for field in fields_list:
            if field == '':
                field = None

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.being_deleted = False
        self.saving_user = None
        self.saving_plugin = ''
        super(Device, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.model and self.model.type == DeviceType.rack:
            if (
                self.parent and
                self.parent.model and
                self.parent.model.type == DeviceType.data_center
            ):
                return "{}::{} ({})".format(
                    self.parent.name, self.name, self.id,
                )
        return "{} ({})".format(self.name, self.id)

    @classmethod
    def create(cls, ethernets=None, sn=None, model=None, model_name=None,
               model_type=None, device=None, allow_stub=False, priority=0,
               **kwargs):
        if 'parent' in kwargs and kwargs['parent'] is None:
            del kwargs['parent']
        if not model and (not model_name or not model_type):
            raise ValueError(
                'Either provide model or model_type and model_name.'
            )
        dev = device
        ethernets = [Eth(*e) for e in (ethernets or []) if
                     is_mac_valid(Eth(*e))]
        if ethernets:
            macs = set([MACAddressField.normalize(eth.mac) for
                        eth in ethernets])
            devs = Device.admin_objects.filter(
                ethernet__mac__in=macs
            ).distinct()
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
            # we don't raise an exception here because blacklisted/missing sn
            # is not enough to fail device's creation
            sn = None
        if not any((sn, ethernets, allow_stub)):
            if sn in SERIAL_BLACKLIST:
                msg = ("You have provided `sn` which is blacklisted. "
                       "Please use a different one.")
            else:
                msg = ("Neither `sn` nor `ethernets` given.  Use `allow_stub` "
                       "to override.")
            raise ValueError(msg)
        if sn:
            try:
                sndev = Device.admin_objects.get(sn=sn)
            except Device.DoesNotExist:
                pass
            else:
                if dev is None:
                    dev = sndev
                elif sndev.id != dev.id:
                    # both devices are properly placed in the tree
                    if any((
                            sndev.parent and dev.parent,
                            # the device found using ethernets (or explicitly
                            # given as `device`) has different sn than `sn`
                            dev.sn and dev.sn != sn,
                            # the device found using `sn` already has other
                            # ethernets
                            sndev.ethernet_set.exists())):
                        raise ValueError(
                            'Conflict of devices %r and %r!' % (dev, sndev)
                        )
                    sndev.delete()
        if model is None:
            model, model_created = DeviceModel.concurrent_get_or_create(
                name=model_name,
                defaults={
                    'type': model_type.id,
                },
            )
        if dev is None:
            dev, created = Device.concurrent_get_or_create(
                sn=sn,
                defaults={
                    'model': model,
                },
            )
        elif dev.deleted:
            # Ignore the priority and undelete even if it was manually deleted
            priorities = dev.get_save_priorities()
            priorities['deleted'] = 0
            dev.update_save_priorities(priorities)
            dev.deleted = False
        if model and model.type != DeviceType.unknown.id:
            dev.model = model
        if not dev.sn and sn:
            dev.sn = sn
        for k, v in kwargs.iteritems():
            if k in ('name', 'last_seen'):
                continue
            setattr(dev, k, v)
        try:
            user = kwargs.get('user')
        except KeyError:
            user = None
        dev.save(user=user, update_last_seen=True, priority=priority)
        for eth in ethernets:
            ethernet, eth_created = Ethernet.concurrent_get_or_create(
                mac=eth.mac,
                defaults={
                    'device': dev,
                },
            )
            ethernet.device = dev
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
                except cls.DoesNotExist:
                    # there is an object with a partial argument match
                    raise e1
                created = False
            else:
                Ethernet.objects.create(
                    device=obj, mac=mac, label='Autocreated'
                )
        return obj, created

    def find_rack(self):
        dev = self
        while dev.parent and dev.parent.model:
            if dev.parent.model.type == DeviceType.rack:
                return dev.parent
            else:
                dev = dev.parent

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
        for ipaddr in self.ipaddress_set.filter(is_management=True).order_by(
            '-address'
        ):
            return ipaddr
        if self.management:
            return self.management
        return None

    @property
    def management_ip(self):
        """
        A backwards-compatible property that gets/sets/deletes management
        IP of a device.
        """
        return self.find_management()

    @management_ip.deleter
    def management_ip(self):
        self.management = None
        self.ipaddress_set.filter(is_management=True).delete()

    @management_ip.setter
    def management_ip(self, value):
        del self.management_ip
        if isinstance(value, IPAddress):
            ipaddr = value
        elif isinstance(value, basestring):
            ipaddr, _ = IPAddress.concurrent_get_or_create(
                address=value
            )
        elif isinstance(value, Iterable):
            hostname, ip = value
            ipaddr, _ = IPAddress.concurrent_get_or_create(address=ip)
            ipaddr.hostname = hostname
        ipaddr.is_management = True
        self.ipaddress_set.add(ipaddr)

    def get_model_name(self):
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
            default_deprecation_kind = DeprecationKind.objects.get(
                default=True
            )
        except DeprecationKind.DoesNotExist:
            return None
        else:
            return default_deprecation_kind

    def is_deprecated(self):
        """ Return True if device is Deprecated """
        if not self.deprecation_date:
            return False
        today_midnight = datetime.datetime.combine(
            datetime.datetime.today(),
            datetime.time(),
        )
        return self.deprecation_date < today_midnight

    def get_core_count(self):
        return sum(cpu.get_cores() for cpu in self.processor_set.all())

    def get_history(self, attr):
        return self.historychange_set.filter(device=self.id, field_name=attr)

    @property
    def ipaddress(self):
        return self.ipaddress_set

    @property
    def rolepropertyvalue(self):
        return self.rolepropertyvalue_set

    @property
    def orientation(self):
        asset = self.get_asset()
        if not asset:
            return ''
        from ralph_assets.models import Orientation
        return Orientation.name_from_id(asset.device_info.orientation)

    def get_components(self):
        details = {}
        details['processors'] = self.processor_set.all()
        details['memory'] = self.memory_set.all()
        details['storages'] = self.storage_set.all()
        details['ethernets'] = self.ethernet_set.all()
        details['fibrechannels'] = self.fibrechannel_set.all()
        return details

    def save(self, sync_fields=True, *args, **kwargs):
        if self.model and self.model.type == DeviceType.blade_server.id:
            if not self.position:
                self.position = self.get_position()
        if self.purchase_date and self.deprecation_kind:
            if isinstance(self.purchase_date, basestring):
                self.purchase_date = datetime.datetime.strptime(
                    self.purchase_date,
                    '%Y-%m-%d %H:%M:%S',
                )
            self.deprecation_date = (
                self.purchase_date + relativedelta(
                    months=self.deprecation_kind.months
                )
            )
        try:
            self.saving_plugin = kwargs.pop('plugin')
        except KeyError:
            # Try to guess the plugin name by the filename of the caller
            for i in range(1, 3):
                try:
                    filename = sys._getframe(1).f_code.co_filename
                except ValueError:
                    break
                if 'plugin' in filename:
                    break
            if filename.endswith('.py'):
                name = os.path.basename(filename)
            else:
                name = filename
            self.saving_plugin = name
        # In case you'd notice that some of the changed fields are mysteriously
        # not saved, check 'save_priorities' property on the device that you're
        # trying to save - if such field is there, and the value associated
        # with it is higher than your current save priority (i.e. 'priority' in
        # kwargs or settings.DEFAULT_SAVE_PRIORITY, in that order), then that's
        # the reason (for more, see the source code of SavePrioritized).
        return super(Device, self).save(*args, **kwargs)

    def set_property(self, symbol, value, user):
        from ralph.business.models import RoleProperty, RolePropertyValue
        try:
            p = self.venture_role.roleproperty_set.get(symbol=symbol)
        except RoleProperty.DoesNotExist:
            p = self.venture.roleproperty_set.get(symbol=symbol)
        if value != p.default and not {value, p.default} == {None, ''}:
            pv, created = RolePropertyValue.concurrent_get_or_create(
                property=p,
                device=self,
            )
            pv.value = value
            pv.save(user=user)
        else:
            try:
                pv = RolePropertyValue.objects.get(
                    property=p,
                    device=self,
                )
            except RolePropertyValue.DoesNotExist:
                pass
            else:
                pv.delete()

    def get_asset(self):
        asset = None
        if self.id and 'ralph_assets' in settings.INSTALLED_APPS:
            from ralph_assets.models import Asset
            try:
                asset = Asset.objects.get(
                    device_info__ralph_device_id=self.id,
                )
            except Asset.DoesNotExist:
                pass
        return asset

    def get_synced_objs_and_fields(self):
        # Implementation of the abstract method from SyncFieldMixin.
        obj = self.get_asset()
        fields = ['service', 'device_environment']
        return [(obj, fields)] if obj else []

    def get_property_set(self):
        props = {}
        if self.venture:
            props.update(dict(
                [
                    (p.symbol, p.default)
                    for p in self.venture.roleproperty_set.all()
                ]
            ))
        if self.venture_role:
            props.update(dict(
                [
                    (p.symbol, p.default)
                    for p in self.venture_role.roleproperty_set.all()
                ]
            ))
        props.update(dict(
            [
                (p.property.symbol, p.value) for p in
                self.rolepropertyvalue_set.all()
            ]
        ))
        return props

    @property
    def url(self):
        return reverse('search', args=('info', self.id))


class Connection(db.Model):

    outbound = db.ForeignKey(
        Device,
        verbose_name=_("connected to device"),
        on_delete=db.PROTECT,
        related_name='outbound_connections',
    )
    inbound = db.ForeignKey(
        Device,
        verbose_name=_("connected device"),
        on_delete=db.PROTECT,
        related_name='inbound_connections',
    )
    connection_type = db.PositiveIntegerField(
        verbose_name=_("connection type"),
        choices=ConnectionType()
    )

    def __unicode__(self):
        return "%s -> %s (%s)" % (
            self.outbound,
            self.inbound,
            self.connection_type
        )


class NetworkConnection(db.Model):

    connection = db.OneToOneField(
        Connection,
        on_delete=db.CASCADE,
    )
    outbound_port = db.CharField(
        verbose_name=_("outbound port"),
        max_length=100
    )
    inbound_port = db.CharField(
        verbose_name=_("inbound port"),
        max_length=100
    )

    def __unicode__(self):
        return "connection from %s on %s to %s on %s" % (
            self.connection.outbound,
            self.outbound_port,
            self.connection.inbound,
            self.inbound_port
        )


class ReadOnlyDevice(Device):

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        assert False, "Cannot save read only models."

    def _fields_as_dict(self):
        return {}


class BaseItem(SavePrioritized, WithConcurrentGetOrCreate, SavingUser):
    name = db.CharField(verbose_name=_("name"), max_length=255)
    venture = db.ForeignKey(
        "business.Venture",
        verbose_name=_("venture"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )
    service = db.ForeignKey(
        ServiceCatalog,
        default=None,
        null=True,
        on_delete=db.PROTECT,
    )
    device_environment = db.ForeignKey(
        DeviceEnvironment,
        default=None,
        null=True,
        on_delete=db.PROTECT,
    )

    class Meta:
        abstract = True
        ordering = ('name',)


class LoadBalancerPool(Named, WithConcurrentGetOrCreate):

    class Meta:
        verbose_name = _("load balancer pool")
        verbose_name_plural = _("load balancer pools")


class LoadBalancerType(SavingUser):
    name = db.CharField(
        verbose_name=_("name"),
        max_length=255,
        unique=True,
    )

    class Meta:
        verbose_name = _("load balancer type")
        verbose_name_plural = _("load balancer types")
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def get_count(self):
        return self.loadbalancervirtualserver_set.count()


class LoadBalancerVirtualServer(BaseItem):
    load_balancer_type = db.ForeignKey(LoadBalancerType, verbose_name=_('load balancer type'))
    device = db.ForeignKey(Device, verbose_name=_("load balancer device"))
    default_pool = db.ForeignKey(LoadBalancerPool, null=True)
    address = db.ForeignKey("IPAddress", verbose_name=_("address"))
    port = db.PositiveIntegerField(verbose_name=_("port"))

    class Meta:
        verbose_name = _("load balancer virtual server")
        verbose_name_plural = _("load balancer virtual servers")
        unique_together = ('address', 'port')

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
        return "{}:{}@{}({})".format(
            self.address.address, self.port, self.pool.name, self.id)


class DatabaseType(SavingUser):
    name = db.CharField(
        verbose_name=_("name"),
        max_length=255,
        unique=True,
    )

    class Meta:
        verbose_name = _("database type")
        verbose_name_plural = _("database types")
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def get_count(self):
        return self.database_set.count()


class Database(BaseItem):
    parent_device = db.ForeignKey(
        Device,
        verbose_name=_("database server"),
    )
    database_type = db.ForeignKey(
        DatabaseType,
        verbose_name=_("database type"),
        related_name='databases',
    )

    class Meta:
        verbose_name = _("database")
        verbose_name_plural = _("databases")

    def __unicode__(self):
        return "{} ({})".format(self.name, self.id)
