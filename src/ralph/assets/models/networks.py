# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import Asset
from ralph.assets.models.mixins import (
    LastSeenMixin,
    NamedMixin,
    TimeStampMixin,
)


def network_validator(value):
    try:
        ipaddr.IPv4Network(value)
    except ipaddr.NetmaskValueError as exc:
        raise ValidationError(exc.message)


@python_2_unicode_compatible
class NetworkKind(NamedMixin, models.Model):
    class Meta:
        verbose_name = _('network kind')
        verbose_name_plural = _('network kinds')
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class NetworkEnvironment(NamedMixin):
    # TODO: more generic
    # data_center = models.ForeignKey(
    #     'DataCenter',
    #     verbose_name=_('data center')
    # )
    queue = models.ForeignKey(
        'DiscoveryQueue',
        verbose_name=_('discovery queue'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    hosts_naming_template = models.CharField(
        max_length=30,
        help_text=_(
            'E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc '
            'h201.dc ... h299.dc h400.dc h401.dc'
        ),
    )
    next_server = models.CharField(
        max_length=32,
        blank=True,
        default='',
        help_text=_('The address for a TFTP server for DHCP.'),
    )
    domain = models.CharField(
        _('domain'),
        max_length=255,
        blank=True,
        null=True,
    )
    remarks = models.TextField(
        verbose_name=_('remarks'),
        help_text=_('Additional information.'),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


@python_2_unicode_compatible
class AbstractNetwork(models.Model):
    """
    Abstract class for networks.
    """
    address = models.CharField(
        _('network address'),
        help_text=_('Presented as string (e.g. 192.168.0.0/24)'),
        max_length=len('xxx.xxx.xxx.xxx/xx'), unique=True,
        validators=[network_validator]
    )
    gateway = models.GenericIPAddressField(
        _('gateway address'), help_text=_('Presented as string.'), blank=True,
        null=True, default=None,
    )
    gateway_as_int = models.PositiveIntegerField(
        _('gateway as int'), null=True, blank=True, default=None,
        editable=False,
    )
    reserved = models.PositiveIntegerField(
        _('reserved'), default=10,
        help_text=_('Number of addresses to be omitted in the automatic '
                    'determination process, counted from the first in range.')
    )
    reserved_top_margin = models.PositiveIntegerField(
        _('reserved (top margin)'), default=0,
        help_text=_('Number of addresses to be omitted in the automatic '
                    'determination process, counted from the last in range.')
    )
    remarks = models.TextField(
        _('remarks'), help_text=_('Additional information.'), blank=True,
        default='',
    )
    terminators = models.ManyToManyField(
        'NetworkTerminator', verbose_name=_('network terminators'),
    )
    vlan = models.PositiveIntegerField(
        _('VLAN number'), null=True, blank=True, default=None,
    )
    # TODO: delete?
    # data_center = models.ForeignKey(
    #     'DataCenter',
    #     verbose_name=_('data center'),
    #     null=True,
    #     blank=True,
    # )
    # TODO: delete?
    # racks = models.ManyToManyField(
    #     'Rack', verbose_name=_('racks'),
    #     # We can't import DeviceType in here, so we use an integer.
    # )
    # TODO: network env
    environment = models.ForeignKey(
        'Environment',
        verbose_name=_('environment'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    min_ip = models.PositiveIntegerField(
        _('smallest IP number'), null=True, blank=True, default=None,
        editable=False,
    )
    max_ip = models.PositiveIntegerField(
        _('largest IP number'), null=True, blank=True, default=None,
        editable=False,
    )
    kind = models.ForeignKey(
        NetworkKind, verbose_name=_('network kind'), on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )
    ignore_addresses = models.BooleanField(
        _('Ignore addresses from this network'),
        default=False,
        help_text=_(
            'Addresses from this network should never be assigned '
            'to any device, because they are not unique.'
        ),
    )
    # custom_dns_servers = models.ManyToManyField(
    #     'dnsedit.DNSServer',
    #     verbose_name=_('custom DNS servers'),
    #     null=True,
    #     blank=True,
    # )
    dhcp_broadcast = models.BooleanField(
        _('Broadcast in DHCP configuration'),
        default=False,
        db_index=True,
    )
    dhcp_config = models.TextField(
        _('DHCP additional configuration'),
        blank=True,
        default='',
    )
    last_scan = models.DateTimeField(
        _('last scan'),
        null=True,
        blank=True,
        default=None,
        editable=False,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.address

    def save(self, *args, **kwargs):
        """
        Override standard save method. Method saves min_ip and max_ip
        depenfing on the self.address.

        Example:
            >>> network = Network.objects.create(
            ...    name='C', address='192.168.1.0/24'
            ... )
            >>> network.min_ip, network.max_ip, network.gateway
            (3232235776, 3232236031, None)
        """
        net = ipaddr.IPNetwork(self.address)
        self.min_ip = int(net.network)
        self.max_ip = int(net.broadcast)
        if self.gateway:
            self.gateway_as_int = int(ipaddr.IPv4Address(self.gateway))
        super(AbstractNetwork, self).save(*args, **kwargs)

    def __contains__(self, what):
        """
        Implements ``in`` operator.

        Arguments:
            what (AbstractNetwork, IPAddress, str)

        Returns:
            True if networks is private, False if is public

        Example:
            >>> network = Network.objects.create(
            ...    name='C', address='192.168.1.0/24'
            ... )
            >>> '192.168.1.1' in network
            True
            >>> '10.0.0.1' in network
            False
        """
        if isinstance(what, AbstractNetwork):
            return what.min_ip >= self.min_ip and what.max_ip <= self.max_ip
        elif isinstance(what, IPAddress):
            ip = what.number
        else:
            ip = int(ipaddr.IPAddress(what))
        return self.min_ip <= ip <= self.max_ip

    def is_private(self):
        """
        Returns:
            True if networks is private, False if is public
        """
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
                # TODO
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


@python_2_unicode_compatible
class Network(NamedMixin, TimeStampMixin, AbstractNetwork, models.Model):
    """
    """
    class Meta:
        verbose_name = _('network')
        verbose_name_plural = _('networks')
        ordering = ('vlan',)

    def __str__(self):
        return '{} ({})'.format(self.name, self.address)


class NetworkTerminator(NamedMixin, models.Model):

    class Meta:
        verbose_name = _('network terminator')
        verbose_name_plural = _('network terminators')
        ordering = ('name',)


class DiscoveryQueue(NamedMixin, models.Model):

    class Meta:
        verbose_name = _('discovery queue')
        verbose_name_plural = _('discovery queues')
        ordering = ('name',)


class IPAddress(LastSeenMixin, TimeStampMixin, models.Model):
    asset = models.ForeignKey(
        Asset, verbose_name=_('asset'), null=True, blank=True,
        default=None, on_delete=models.SET_NULL,
    )
    address = models.GenericIPAddressField(
        _('IP address'), help_text=_('Presented as string.'), unique=True,
        blank=True, null=True, default=None,
    )
    number = models.BigIntegerField(
        _('IP address'), help_text=_('Presented as int.'), editable=False,
        unique=True,
    )
    # TODO: hostname in asset?
    # hostname = models.CharField(
    #     _('hostname'), max_length=255, null=True, blank=True, default=None,
    # )
    # hostname.max_length vide /usr/include/bits/posix1_lim.h
    snmp_name = models.TextField(
        _('name from SNMP'), null=True, blank=True, default=None,
    )
    snmp_community = models.CharField(
        _('SNMP community'), max_length=64, null=True, blank=True,
        default=None,
    )
    snmp_version = models.CharField(
        _('SNMP version'),
        max_length=5,
        null=True,
        blank=True,
        default=None,
    )
    http_family = models.TextField(
        _('family from HTTP'), null=True, blank=True, default=None,
        max_length=64,
    )
    is_management = models.BooleanField(
        _('This is a management address'),
        default=False,
    )
    dns_info = models.TextField(
        _('information from DNS TXT fields'), null=True, blank=True,
        default=None,
    )
    network = models.ForeignKey(
        Network, verbose_name=_('network'), null=True, blank=True,
        default=None,
    )
    last_plugins = models.TextField(_('last plugins'), blank=True)
    dead_ping_count = models.IntegerField(_('dead ping count'), default=0)
    is_buried = models.BooleanField(_('Buried from autoscan'), default=False)
    # scan_summary = models.ForeignKey(
    #     'scan.ScanSummary',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    # )
    is_public = models.BooleanField(
        _('This is a public address'),
        default=False,
        editable=False,
    )
    # TODO: old venture
    # configuration_path = models.CharField(
    #     _('configuration path'),
    #     max_length=100,
    #     help_text=_('Path to configuration for e.g. puppet, chef.'),
    # )
    # TODO: more generic name
    # last_puppet = models.DateTimeField(
    #     _('last puppet check'), null=True, blank=True, default=None,
    # )

    class Meta:
        verbose_name = _('IP address')
        verbose_name_plural = _('IP addresses')

    def __str__(self):
        return '{} ({})'.format(self.hostname, self.address)
