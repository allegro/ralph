#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Network-related models ."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models as db
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
import ipaddr
from lck.django.common.models import (
    TimeTrackable, Named, WithConcurrentGetOrCreate, SavePrioritized,
)

from ralph.util import network
from ralph.discovery.models_util import LastSeen


class NetworkKind(Named):
    icon = db.CharField(
        _("icon"), max_length=32, null=True, blank=True, default=None,
    )

    class Meta:
        verbose_name = _("network kind")
        verbose_name_plural = _("network kinds")
        ordering = ('name',)


class AbstractNetwork(db.Model):
    address = db.CharField(
        _("network address"),
        help_text=_("Presented as string (e.g. 192.168.0.0/24)"),
        max_length=len("xxx.xxx.xxx.xxx/xx"), unique=True,
    )
    gateway = db.IPAddressField(
        _("gateway address"), help_text=_("Presented as string."), blank=True,
        null=True, default=None,
    )
    reserved = db.PositiveIntegerField(
        _("reserved"), default=10,
        help_text=_("Number of addresses to be omitted in the automatic "
                    "determination process, counted from the first in range.")
    )
    reserved_top_margin = db.PositiveIntegerField(
        _("reserved (top margin)"), default=0,
        help_text=_("Number of addresses to be omitted in the automatic "
                    "determination process, counted from the last in range.")
    )
    remarks = db.TextField(
        _("remarks"), help_text=_("Additional information."), blank=True,
        default="",
    )
    terminators = db.ManyToManyField(
        "NetworkTerminator", verbose_name=_("network terminators"),
    )
    vlan = db.PositiveIntegerField(
        _("VLAN number"), null=True, blank=True, default=None,
    )
    data_center = db.ForeignKey("DataCenter", verbose_name=_("data center"))
    min_ip = db.PositiveIntegerField(
        _("smallest IP number"), null=True, blank=True, default=None,
    )
    max_ip = db.PositiveIntegerField(
        _("largest IP number"), null=True, blank=True, default=None,
    )
    kind = db.ForeignKey(
        NetworkKind, verbose_name=_("network kind"), on_delete=db.SET_NULL,
        null=True, blank=True, default=None,
    )
    queue = db.ForeignKey(
        "DiscoveryQueue", verbose_name=_("discovery queue"), null=True,
        blank=True, default=None, on_delete=db.SET_NULL,
    )
    racks = db.ManyToManyField(
        'discovery.Device', verbose_name=_("racks"),
        # We can't import DeviceType in here, so we use an integer.
        limit_choices_to={
            'model__type': 1,
            'deleted': False,
        },  # DeviceType.rack.id
    )
    ignore_addresses = db.BooleanField(
        _("Ignore addresses from this network"),
        default=False,
        help_text=_(
            "Addresses from this network should never be assigned "
            "to any device, because they are not unique."
        ),
    )
    dhcp_config = db.TextField(
        _("DHCP configuration"), blank=True, default='',
    )
    last_scan = db.DateTimeField(
        _("last scan"), null=True, blank=True, default=None,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        net = ipaddr.IPNetwork(self.address)
        self.min_ip = int(net.network)
        self.max_ip = int(net.broadcast)
        super(AbstractNetwork, self).save(*args, **kwargs)

    def __contains__(self, what):
        if isinstance(what, AbstractNetwork):
            return what.min_ip >= self.min_ip and what.max_ip <= self.max_ip
        elif isinstance(what, IPAddress):
            ip = what.number
        else:
            ip = int(ipaddr.IPAddress(what))
        return self.min_ip <= ip <= self.max_ip

    def is_private(self):
        ip = ipaddr.IPAddress(self.address.split('/')[0])
        return (
            ip in ipaddr.IPNetwork('10.0.0.0/8') or
            ip in ipaddr.IPNetwork('172.16.0.0/12') or
            ip in ipaddr.IPNetwork('192.168.0.0/16')
        )

    @classmethod
    def from_ip(cls, ip):
        """Find the smallest network containing that IP."""

        return cls.all_from_ip(ip)[0]

    @classmethod
    def all_from_ip(cls, ip):
        """Find all networks for this IP."""

        ip_int = int(ipaddr.IPAddress(ip))
        nets = cls.objects.filter(
            min_ip__lte=ip_int,
            max_ip__gte=ip_int
        ).order_by('min_ip', '-max_ip')
        return nets

    @property
    def network(self):
        return ipaddr.IPNetwork(self.address)

    def clean(self, *args, **kwargs):
        super(AbstractNetwork, self).clean(*args, **kwargs)
        try:
            ipaddr.IPNetwork(self.address)
        except ValueError:
            raise ValidationError(_("The address value specified is not a "
                                    "valid network."))

class Network(Named, AbstractNetwork, TimeTrackable,
              WithConcurrentGetOrCreate):
    class Meta:
        verbose_name = _("network")
        verbose_name_plural = _("networks")
        ordering = ('vlan',)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.address)


class NetworkTerminator(Named):
    class Meta:
        verbose_name = _("network terminator")
        verbose_name_plural = _("network terminators")
        ordering = ('name',)


class DataCenter(Named):
    hosts_naming_template = db.CharField(
        max_length=30, default="h<10000,19999>.dc",
        help_text=_(
            "E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc "
            "h201.dc ... h299.dc h400.dc h401.dc"
        )
    )
    next_server = db.CharField(
        max_length=32,
        blank=True,
        default='',
        help_text=_("The address for a TFTP server for DHCP."),
    )

    class Meta:
        verbose_name = _("data center")
        verbose_name_plural = _("data centers")
        ordering = ('name',)


class DiscoveryQueue(Named):
    class Meta:
        verbose_name = _("discovery queue")
        verbose_name_plural = _("discovery queues")
        ordering = ('name',)


def validate_network_address(sender, instance, **kwargs):
    instance.full_clean()
db.signals.pre_save.connect(validate_network_address, sender=Network)


class IPAddress(LastSeen, TimeTrackable, WithConcurrentGetOrCreate):
    address = db.IPAddressField(
        _("IP address"), help_text=_("Presented as string."), unique=True,
        blank=True, null=True, default=None,
    )
    number = db.BigIntegerField(
        _("IP address"), help_text=_("Presented as int."), editable=False,
        unique=True,
    )
    hostname = db.CharField(
        _("hostname"), max_length=255, null=True, blank=True, default=None,
    )
    # hostname.max_length vide /usr/include/bits/posix1_lim.h
    snmp_name = db.TextField(
        _("name from SNMP"), null=True, blank=True, default=None,
    )
    snmp_community = db.CharField(
        _("SNMP community"), max_length=64, null=True, blank=True,
        default=None,
    )
    device = db.ForeignKey(
        'Device', verbose_name=_("device"), null=True, blank=True,
        default=None, on_delete=db.SET_NULL,
    )
    http_family = db.TextField(
        _('family from HTTP'),  null=True, blank=True, default=None,
        max_length=64,
    )
    is_management = db.BooleanField(
        _("This is a management address"),
        default=False,
    )
    dns_info = db.TextField(
        _('information from DNS TXT fields'), null=True, blank=True,
        default=None,
    )
    last_puppet = db.DateTimeField(
        _("last puppet check"), null=True, blank=True, default=None,
    )
    network = db.ForeignKey(
        Network, verbose_name=_("network"), null=True, blank=True,
        default=None,
    )
    last_plugins = db.TextField(_("last plugins"),  blank=True)
    dead_ping_count = db.IntegerField(_("dead ping count"), default=0)
    is_buried = db.BooleanField(_("Buried from autoscan"), default=False)

    class Meta:
        verbose_name = _("IP address")
        verbose_name_plural = _("IP addresses")

    def __unicode__(self):
        return "{} ({})".format(self.hostname, self.address)

    def save(self, allow_device_change=True, *args, **kwargs):
        if not allow_device_change:
            self.assert_same_device()
        if not self.address:
            self.address = network.hostname(self.hostname, reverse=True)
        if not self.hostname:
            self.hostname = network.hostname(self.address)
        self.number = int(ipaddr.IPAddress(self.address))
        try:
            self.network = Network.from_ip(self.address)
        except IndexError:
            self.network = None
        if self.network and self.network.ignore_addresses:
            self.device = None
        super(IPAddress, self).save(*args, **kwargs)

    def assert_same_device(self):
        if not self.id or 'device_id' not in self.dirty_fields:
            return
        dirty_devid = self.dirty_fields['device_id']
        if not dirty_devid or dirty_devid == self.device_id:
            return
        # The addresses from outside of our defined networks can change freely
        if self.network is None:
            try:
                self.network = Network.from_ip(self.address)
            except IndexError:
                return
        raise IntegrityError(
            "Trying to assign device ID #{} for IP {} but device ID #{} "
            "already assigned.".format(self.device_id, self, dirty_devid),
        )


class IPAlias(SavePrioritized, WithConcurrentGetOrCreate):
    address = db.ForeignKey("IPAddress", related_name="+")
    hostname = db.CharField(_("hostname"), max_length=255)
    # hostname.max_length vide /usr/include/bits/posix1_lim.h

    class Meta:
        verbose_name = _("IP alias")
        verbose_name_plural = _("IP aliases")
