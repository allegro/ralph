# -*- coding: utf-8 -*-
import ipaddress
from itertools import chain

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.assets.models.assets import BaseObject
from ralph.data_center.fields import IPNetwork
from ralph.data_center.models.choices import IPAddressStatus
from ralph.data_center.models.physical import DataCenter, Rack
from ralph.lib import network as network_tools
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    LastSeenMixin,
    NamedMixin,
    TimeStampMixin
)


class NetworkKind(NamedMixin, models.Model):
    class Meta:
        verbose_name = _('network kind')
        verbose_name_plural = _('network kinds')
        ordering = ('name',)

    def __str__(self):
        return self.name


class NetworkEnvironment(NamedMixin):
    data_center = models.ForeignKey(
        DataCenter,
        verbose_name=_('data center')
    )
    queue = models.ForeignKey(
        'DiscoveryQueue',
        verbose_name=_('discovery queue'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    hosts_naming_template = models.CharField(
        verbose_name=_('hosts naming template'),
        max_length=30,
        help_text=_(
            'E.g. h<200,299>.dc|h<400,499>.dc will produce: h200.dc '
            'h201.dc ... h299.dc h400.dc h401.dc'
        ),
    )
    next_server = models.CharField(
        verbose_name=_('next server'),
        max_length=32,
        blank=True,
        default='',
        help_text=_('The address for a TFTP server for DHCP.'),
    )
    domain = models.CharField(
        verbose_name=_('domain'),
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


class NetworkMixin(object):
    _parent_attr = None

    def _assign_parent(self):
        parent = getattr(self, self._parent_attr)
        if not parent or self.pk:
            setattr(self, self._parent_attr, self.get_network())

    def search_networks(self):
        raise NotImplementedError()

    def get_network(self):
        network = None
        networks = self.search_networks()
        if networks:
            network = networks[0]
        return network


class Network(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin,
    NetworkMixin,
    MPTTModel,
    models.Model
):
    """
    Class for networks.
    """
    _parent_attr = 'parent'
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        editable=False,
    )
    address = IPNetwork(
        verbose_name=_('network address'),
        help_text=_('Presented as string (e.g. 192.168.0.0/24)'),
    )
    remarks = models.TextField(
        verbose_name=_('remarks'),
        help_text=_('Additional information.'),
        blank=True,
        default='',
    )
    terminators = models.ManyToManyField(
        'NetworkTerminator',
        verbose_name=_('network terminators'),
        blank=True
    )
    vlan = models.PositiveIntegerField(
        verbose_name=_('VLAN number'),
        null=True,
        blank=True,
        default=None,
    )
    racks = models.ManyToManyField(
        Rack,
        verbose_name=_('racks'),
        blank=True,
    )
    network_environment = models.ForeignKey(
        NetworkEnvironment,
        verbose_name=_('environment'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    min_ip = models.DecimalField(
        verbose_name=_('smallest IP number'),
        null=True,
        blank=True,
        editable=False,
        max_digits=39,
        decimal_places=0,
        default=None,
    )
    max_ip = models.DecimalField(
        verbose_name=_('largest IP number'),
        null=True,
        blank=True,
        editable=False,
        max_digits=39,
        decimal_places=0,
        default=None,
    )
    kind = models.ForeignKey(
        NetworkKind,
        verbose_name=_('network kind'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )
    dhcp_broadcast = models.BooleanField(
        verbose_name=_('Broadcast in DHCP configuration'),
        default=False,
        db_index=True,
    )

    @cached_property
    def network(self):
        return ipaddress.ip_network(self.address, strict=False)

    @property
    def network_address(self):
        return self.network.network_address

    @property
    def broadcast_address(self):
        return self.network.broadcast_address

    @property
    def netmask(self):
        return self.network.prefixlen

    @property
    def gateway(self):
        ip = self.ips.filter(is_gateway=True).first()
        return ip.ip if ip else None

    @property
    def size(self):
        # TODO: IPv6
        if not self.min_ip and not self.max_ip or self.netmask == 32:
            return 0
        if self.netmask == 31:
            return 2
        return self.max_ip - self.min_ip - 1

    class Meta:
        verbose_name = _('network')
        verbose_name_plural = _('networks')
        unique_together = ('min_ip', 'max_ip')

    def __str__(self):
        return '{} ({})'.format(self.name, self.address)

    def save(self, *args, **kwargs):
        """
        Override standard save method. Method saves min_ip and max_ip
        depenfing on the self.address.

        Example:
            >>> network = Network.objects.create(
            ...     name='C', address='192.168.1.0/24'
            ... )
            >>> network.min_ip, network.max_ip, network.gateway
            (3232235776, 3232236031, None)
        """
        self.min_ip = int(self.network_address)
        self.max_ip = int(self.broadcast_address)
        self._assign_parent()
        super(Network, self).save(*args, **kwargs)
        self._assign_ips_to_network()

    def _assign_ips_to_network(self):
        IPAddress.objects.exclude(
            network=self
        ).filter(
            number__gte=self.min_ip,
            number__lte=self.max_ip
        ).update(
            network=self
        )

    def get_subnetworks(self):
        return self.get_descendants()

    def reserve_margin_addresses(self, bottom_count=None, top_count=None):
        ips = []
        exists_ips = set(IPAddress.objects.filter(
            Q(number__gte=self.min_ip, number__lte=self.min_ip + bottom_count) |
            Q(number__gte=self.max_ip - top_count, number__lte=self.max_ip)
        ).values_list('number', flat=True))
        to_create = set(chain.from_iterable([
            range(int(self.min_ip + 1), int(self.min_ip + bottom_count)),
            range(int(self.max_ip - top_count), int(self.max_ip - 1))
        ]))
        to_create = to_create - exists_ips
        for ip_as_int in to_create:
            ips.append(IPAddress(
                number=ip_as_int,
                network=self,
                status=IPAddressStatus.reserved
            ))
        IPAddress.objects.bulk_create(ips)
        return len(to_create), exists_ips - to_create

    def get_first_free_ip(self):
        used_ips = list(
            self.ips.values_list('number', flat=True).order_by('number')
        )
        min_ip = int(self.min_ip if self.netmask == 31 else self.min_ip + 1)
        max_ip = int(self.max_ip + 1 if self.netmask == 31 else self.max_ip)
        ip_as_int = None
        for ip_as_int in range(min_ip, max_ip):
            if ip_as_int not in used_ips:
                break
        # TODO: do it better
        last = ip_as_int in used_ips
        return (
            ipaddress.ip_address(ip_as_int)
            if ip_as_int and not last else None
        )

    def search_networks(self):
        nets = Network.objects.filter(
            min_ip__lte=self.min_ip,
            max_ip__gte=self.max_ip
        ).exclude(pk=self.id).order_by('-min_ip', 'max_ip')
        return nets


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


class IPAddress(LastSeenMixin, TimeStampMixin, NetworkMixin, models.Model):
    _parent_attr = 'network'

    base_object = models.ForeignKey(
        BaseObject,
        verbose_name=_('Base object'),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    network = models.ForeignKey(
        Network,
        null=True,
        default=None,
        editable=False,
        related_name='ips',
        on_delete=models.SET_NULL,
    )
    address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
        help_text=_('Presented as string.'),
        unique=True,
        blank=False,
        null=True,
        default=None,
    )
    hostname = models.CharField(
        verbose_name=_('Hostname'),
        max_length=255,
        null=True,
        blank=True,
        default=None,
    )
    number = models.DecimalField(
        verbose_name=_('IP address'),
        help_text=_('Presented as int.'),
        editable=False,
        unique=True,
        max_digits=39,
        decimal_places=0,
        default=None,
    )
    is_management = models.BooleanField(
        verbose_name=_('This is a management address'),
        default=False,
    )
    is_public = models.BooleanField(
        verbose_name=_('This is a public address'),
        default=False,
        editable=False,
    )
    is_gateway = models.BooleanField(
        verbose_name=_('This is a gateway address'),
        default=False,
        editable=False,
    )
    status = models.PositiveSmallIntegerField(
        default=IPAddressStatus.used.id,
        choices=IPAddressStatus(),
    )

    class Meta:
        verbose_name = _('IP address')
        verbose_name_plural = _('IP addresses')

    def __str__(self):
        return self.address

    def save(self, *args, **kwargs):
        if settings.CHECK_IP_HOSTNAME_ON_SAVE:
            if not self.address and self.hostname:
                self.address = network_tools.hostname(
                    self.hostname, reverse=True
                )
            if not self.hostname and self.address:
                self.hostname = network_tools.hostname(self.address)
        if self.number and not self.address:
            self.address = ipaddress.ip_address(self.number)
        else:
            self.number = int(ipaddress.ip_address(self.address))
        ip = ipaddress.ip_address(self.address)
        self._assign_parent()
        self.is_public = not ip.is_private
        super(IPAddress, self).save(*args, **kwargs)

    @property
    def ip(self):
        return ipaddress.ip_address(self.address)

    def search_networks(self):
        int_value = int(self.ip)
        nets = Network.objects.filter(
            min_ip__lte=int_value,
            max_ip__gte=int_value
        ).order_by('-min_ip', 'max_ip')
        return nets
