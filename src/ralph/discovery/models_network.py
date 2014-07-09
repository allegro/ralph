#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Network-related models ."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
import urllib

from django.core.exceptions import ValidationError
from django.db import models as db
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    TimeTrackable, Named, WithConcurrentGetOrCreate, SavePrioritized,
)

from ralph.util import network
from ralph.discovery.models_util import LastSeen


def get_network_tree(qs=None):
    """
    Returns tree of networks based on L3 containment.
    """
    if not qs:
        qs = Network.objects.all()
    tree = []
    all_networks = [
        (net.max_ip, net.min_ip, net)
        for net in qs.order_by("min_ip", "-max_ip")
    ]

    def get_subnetworks_qs(network):
        for net in all_networks:
            if net[0] == network.max_ip and net[1] == network.min_ip:
                continue
            if net[0] <= network.max_ip and net[1] >= network.min_ip:
                yield net[2]

    def recursive_tree(network):
        subs = []
        sub_qs = get_subnetworks_qs(network)
        subnetworks = network.get_subnetworks(networks=sub_qs)
        subs = [
            {
                'network': sub,
                'subnetworks': recursive_tree(sub)
            } for sub in subnetworks
        ]
        for i, net in enumerate(all_networks):
            if net[0] == network.max_ip and net[1] == network.min_ip:
                all_networks.pop(i)
                break
        return subs

    while True:
        try:
            tree.append({
                'network': all_networks[0][2],
                'subnetworks': recursive_tree(all_networks[0][2])
            })
        except IndexError:
            # recursive tree uses pop, so at some point all_networks[0]
            # will rise IndexError, therefore algorithm is finished
            break
    return tree


class Environment(Named):
    data_center = db.ForeignKey("DataCenter", verbose_name=_("data center"))
    queue = db.ForeignKey(
        "DiscoveryQueue",
        verbose_name=_("discovery queue"),
        null=True,
        blank=True,
        on_delete=db.SET_NULL,
    )
    hosts_naming_template = db.CharField(
        max_length=30,
        help_text=_(
            "E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc "
            "h201.dc ... h299.dc h400.dc h401.dc"
        ),
    )
    next_server = db.CharField(
        max_length=32,
        blank=True,
        default='',
        help_text=_("The address for a TFTP server for DHCP."),
    )
    domain = db.CharField(
        _('domain'),
        max_length=255,
        blank=True,
        null=True,
    )
    remarks = db.TextField(
        verbose_name=_("remarks"),
        help_text=_("Additional information."),
        blank=True,
        null=True,
    )

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


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
    gateway_as_int = db.PositiveIntegerField(
        _("gateway as int"), null=True, blank=True, default=None,
        editable=False,
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
    data_center = db.ForeignKey(
        "DataCenter",
        verbose_name=_("data center"),
        null=True,
        blank=True,
    )
    environment = db.ForeignKey(
        "Environment",
        verbose_name=_("environment"),
        null=True,
        blank=True,
        on_delete=db.SET_NULL,
    )
    min_ip = db.PositiveIntegerField(
        _("smallest IP number"), null=True, blank=True, default=None,
        editable=False,
    )
    max_ip = db.PositiveIntegerField(
        _("largest IP number"), null=True, blank=True, default=None,
        editable=False,
    )
    kind = db.ForeignKey(
        NetworkKind, verbose_name=_("network kind"), on_delete=db.SET_NULL,
        null=True, blank=True, default=None,
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
    custom_dns_servers = db.ManyToManyField(
        'dnsedit.DNSServer',
        verbose_name=_('custom DNS servers'),
        null=True,
        blank=True,
    )
    dhcp_broadcast = db.BooleanField(
        _("Broadcast in DHCP configuration"),
        default=False,
        db_index=True,
    )
    dhcp_config = db.TextField(
        _("DHCP additional configuration"),
        blank=True,
        default='',
    )
    last_scan = db.DateTimeField(
        _("last scan"),
        null=True,
        blank=True,
        default=None,
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        net = ipaddr.IPNetwork(self.address)
        self.min_ip = int(net.network)
        self.max_ip = int(net.broadcast)
        if self.gateway:
            self.gateway_as_int = int(ipaddr.IPv4Address(self.gateway))
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

    def get_subnetworks(self, networks=None):
        """
        Return list of all L3 subnetworks this network contains.
        Only first level of children networks are returned.
        """
        if not networks:
            networks = Network.objects.filter(
                data_center=self.data_center,
                min_ip__gte=self.min_ip,
                max_ip__lte=self.max_ip,
            ).exclude(
                pk=self.id,
            ).order_by('-min_ip', 'max_ip')
        subnets = sorted(list(networks), key=lambda net: net.get_netmask())
        new_subnets = list(subnets)
        for net, netw in enumerate(subnets):
            net_address = ipaddr.IPNetwork(netw.address)
            for i, sub in enumerate(subnets):
                sub_addr = ipaddr.IPNetwork(sub.address)
                if sub_addr != net_address and sub_addr in net_address:
                    if sub in new_subnets:
                        new_subnets.remove(sub)
        new_subnets = sorted(new_subnets, key=lambda net: net.min_ip)
        return new_subnets

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
        ).order_by('-min_ip', 'max_ip')
        return nets

    @property
    def network(self):
        return ipaddr.IPNetwork(self.address)

    def get_total_ips(self):
        """
        Get total amount of addresses in this network.
        """
        return self.max_ip - self.min_ip

    def get_subaddresses(self):
        subnetworks = self.get_subnetworks()
        addresses = list(IPAddress.objects.filter(
            number__gte=self.min_ip,
            number__lte=self.max_ip,
        ).order_by("number"))
        new_addresses = list(addresses)
        for addr in addresses:
            for subnet in subnetworks:
                if addr in subnet and addr in new_addresses:
                    new_addresses.remove(addr)
        return new_addresses

    def get_free_ips(self):
        """
        Get number of free addresses in network.
        """
        subnetworks = self.get_subnetworks()
        total_ips = self.get_total_ips()
        for subnet in subnetworks:
            total_ips -= subnet.get_total_ips()
        addresses = self.get_subaddresses()
        total_ips -= len(addresses)
        total_ips -= self.reserved_top_margin + self.reserved
        return total_ips

    def get_ip_usage_range(self):
        """
        Returns list of entities this network contains (addresses and subnets)
        ordered by its address or address range.
        """
        contained = []
        contained.extend(self.get_subnetworks())
        contained.extend(self.get_subaddresses())

        def sorting_key(obj):
            if isinstance(obj, Network):
                return obj.min_ip
            elif isinstance(obj, IPAddress):
                return obj.number
            else:
                raise TypeError("Type not supported")

        return sorted(contained, key=sorting_key)

    def get_ip_usage_aggegated(self):
        """
        Aggregates network usage range - combines neighboring addresses to
        a single entitiy and appends blocks of free addressations.
        """
        address_range = self.get_ip_usage_range()
        ranges_and_networks = []
        ip_range = []
        for addr in address_range:
            if isinstance(addr, IPAddress):
                if ip_range and not addr.number - 1 in ip_range:
                    ranges_and_networks.append((ip_range[0], ip_range[-1], 1))
                    ip_range = []
                ip_range.append(addr.number)
            else:
                if ip_range:
                    ranges_and_networks.append((ip_range[0], ip_range[-1], 1))
                    ip_range = []
                ranges_and_networks.append((addr.min_ip, addr.max_ip, addr))

        def f(a):
            if a[2] == 0:
                range_type = "free"
            elif a[2] == 1:
                range_type = "addr"
            else:
                range_type = a[2]
            return {
                'range_start': str(ipaddr.IPAddress(a[0])),
                'range_end': str(ipaddr.IPAddress(a[1])),
                'type': range_type,
                'amount': a[1] - a[0] + 1,
            }

        min_ip = self.min_ip
        parsed = []
        for i, range_or_net in enumerate(ranges_and_networks):
            if range_or_net[0] != min_ip:
                parsed.append(f((min_ip, range_or_net[0] - 1, 0)))
            parsed.append(f(range_or_net))
            min_ip = range_or_net[1] + 1
        if ranges_and_networks and ranges_and_networks[-1][1] < self.max_ip:
            parsed.append(f((ranges_and_networks[-1][1] + 1, self.max_ip, 0)))
        if not ranges_and_networks:
            # this network is empty, lets append big, free block
            parsed.append(f((self.min_ip, self.max_ip, 0)))
        return parsed

    def get_netmask(self):
        try:
            mask = self.address.split("/")[1]
            return int(mask)
        except (ValueError, IndexError):
            return None

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

    def get_absolute_url(self):
        args = [urllib.quote(self.name.encode('utf-8'), ''), 'info']
        return reverse("networks", args=args)


class NetworkTerminator(Named):

    class Meta:
        verbose_name = _("network terminator")
        verbose_name_plural = _("network terminators")
        ordering = ('name',)


class DataCenter(Named):

    def __unicode__(self):
        return self.name

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
    return

    # clearing cache items for networks sidebar(24 hour cache)
    ns_items_key = 'cache_network_sidebar_items'
    if ns_items_key in cache:
        cache.delete(ns_items_key)

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
    snmp_version = db.CharField(
        _("SNMP version"),
        max_length=5,
        null=True,
        blank=True,
        default=None,
    )
    device = db.ForeignKey(
        'Device', verbose_name=_("device"), null=True, blank=True,
        default=None, on_delete=db.SET_NULL,
    )
    http_family = db.TextField(
        _('family from HTTP'), null=True, blank=True, default=None,
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
    last_plugins = db.TextField(_("last plugins"), blank=True)
    dead_ping_count = db.IntegerField(_("dead ping count"), default=0)
    is_buried = db.BooleanField(_("Buried from autoscan"), default=False)
    scan_summary = db.ForeignKey(
        'scan.ScanSummary',
        on_delete=db.SET_NULL,
        null=True,
        blank=True,
    )
    is_public = db.BooleanField(
        _("This is a public address"),
        default=False,
        editable=False,
    )
    venture = db.ForeignKey(
        'business.Venture',
        verbose_name=_("venture"),
        null=True,
        blank=True,
        default=None,
        on_delete=db.SET_NULL,
    )

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
        ip = ipaddr.IPAddress(self.address)
        self.is_public = not ip.is_private
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

    # We overwrite the following method. If the address is not bound to
    # any device or venture, we can delete it and create new.
    def _perform_unique_checks(self, *args, **kwargs):
        try:
            existing = type(self).objects.get(address=self.address)
        except type(self).DoesNotExist:
            return
        if existing == self:
            return
        elif existing.device:
            return {'address': [_('There exists a device with this address')]}
        elif existing.venture:
            return {'address': [_('This address is a public one')]}


class IPAlias(SavePrioritized, WithConcurrentGetOrCreate):
    address = db.ForeignKey("IPAddress", related_name="+")
    hostname = db.CharField(_("hostname"), max_length=255)
    # hostname.max_length vide /usr/include/bits/posix1_lim.h

    class Meta:
        verbose_name = _("IP alias")
        verbose_name_plural = _("IP aliases")
