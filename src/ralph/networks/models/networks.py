# -*- coding: utf-8 -*-
import ipaddress
import socket
import struct
from itertools import chain

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.assets.models import AssetLastHostname, Ethernet
from ralph.lib import network as network_tools
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    LastSeenMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.networks.fields import IPNetwork
from ralph.networks.models.choices import IPAddressStatus


class NetworkKind(NamedMixin, models.Model):
    class Meta:
        verbose_name = _('network kind')
        verbose_name_plural = _('network kinds')
        ordering = ('name',)


class NetworkEnvironment(TimeStampMixin, NamedMixin, models.Model):
    data_center = models.ForeignKey(
        'data_center.DataCenter',
        verbose_name=_('data center')
    )
    queue = models.ForeignKey(
        'DiscoveryQueue',
        verbose_name=_('discovery queue'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    hostname_template_counter_length = models.PositiveIntegerField(
        verbose_name=_('hostname template counter length'),
        default=4,
    )
    hostname_template_prefix = models.CharField(
        verbose_name=_('hostname template prefix'),
        max_length=30,
    )
    hostname_template_postfix = models.CharField(
        verbose_name=_('hostname template postfix'),
        max_length=30,
        help_text=_(
            'This value will be used as a postfix when generating new hostname '
            'in this network environment. For example, when prefix is "s1", '
            'postfix is ".mydc.net" and counter length is 4, following '
            ' hostnames will be generated: s10000.mydc.net, s10001.mydc.net, ..'
            ', s19999.mydc.net.'
        )
    )
    domain = NullableCharField(
        verbose_name=_('domain'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Used in DHCP configuration.'),
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

    @property
    def next_free_hostname(self):
        """
        Retrieve next free hostname
        """
        return AssetLastHostname.get_next_free_hostname(
            self.hostname_template_prefix,
            self.hostname_template_postfix,
            self.hostname_template_counter_length
        )

    def issue_next_free_hostname(self):
        """
        Retrieve and reserve next free hostname
        """
        return AssetLastHostname.increment_hostname(
            self.hostname_template_prefix,
            self.hostname_template_postfix,
        ).formatted_hostname(self.hostname_template_counter_length)


class NetworkMixin(object):
    _parent_attr = None

    def _assign_parent(self):
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
    # TODO: create ManyToManyBaseObjectField to avoid through table
    terminators = models.ManyToManyField(
        'assets.BaseObject',
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
        'data_center.Rack',
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
    network_environment._autocomplete = False
    min_ip = models.DecimalField(
        verbose_name=_('smallest IP number'),
        editable=False,
        max_digits=39,
        decimal_places=0,
    )
    max_ip = models.DecimalField(
        verbose_name=_('largest IP number'),
        editable=False,
        max_digits=39,
        decimal_places=0,
    )
    kind = models.ForeignKey(
        NetworkKind,
        verbose_name=_('network kind'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    dhcp_broadcast = models.BooleanField(
        verbose_name=_('Broadcast in DHCP configuration'),
        default=True,
        db_index=True,
    )
    service_env = models.ForeignKey(
        'assets.ServiceEnvironment', related_name='networks', null=True,
        default=None, blank=True,
    )
    dns_servers = models.ManyToManyField(
        'dhcp.DNSServer',
        verbose_name=_('DNS servers'),
        blank=True,
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
    def netmask_dot_decimal(self):
        """Returns netmask in dot-decimal notaion (e.g. 255.255.255.0)."""
        return socket.inet_ntoa(
            struct.pack('>I', (0xffffffff << (32 - self.netmask)) & 0xffffffff)
        )

    @property
    def gateway(self):
        ip = self.ips.filter(is_gateway=True).first()
        return ip.ip if ip else None

    @property
    def domain(self):
        net_env = self.network_environment
        return net_env.domain if net_env else None

    @property
    def data_center(self):
        if not self.network_environment:
            return None
        return self.network_environment.data_center

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
        enable_save_descendants = kwargs.pop('enable_save_descendants', True)
        self.min_ip = int(self.network_address)
        self.max_ip = int(self.broadcast_address)
        self._assign_parent()
        super(Network, self).save(*args, **kwargs)
        self._assign_ips_to_network()
        if enable_save_descendants:
            self._update_subnetworks_parent()

    def delete(self):
        # Save fake address so that all children of network changed its
        # parent, only then network is removed.
        with transaction.atomic():
            self.address = '0.0.0.0/32'
            self.save()
            super().delete()

    def _update_subnetworks_parent(self):
        for network in self.__class__.objects.all():
            network.save(enable_save_descendants=False)

    def _assign_ips_to_network(self):
        self, IPAddress.objects.exclude(
            network=self,
        ).exclude(
            network__in=self.get_subnetworks()
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
        existing_ips = set(IPAddress.objects.filter(
            Q(
                number__gte=self.min_ip,
                number__lte=self.min_ip + bottom_count
            ) |
            Q(number__gte=self.max_ip - top_count, number__lte=self.max_ip)
        ).values_list('number', flat=True))
        to_create = set(chain.from_iterable([
            range(int(self.min_ip + 1), int(self.min_ip + bottom_count)),
            range(int(self.max_ip - top_count), int(self.max_ip - 1))
        ]))
        to_create = to_create - existing_ips
        for ip_as_int in to_create:
            ips.append(IPAddress(
                address=str(ipaddress.ip_address(ip_as_int)),
                number=ip_as_int,
                network=self,
                status=IPAddressStatus.reserved
            ))
        IPAddress.objects.bulk_create(ips)
        # TODO: handle decreasing count
        return len(to_create), existing_ips - to_create

    def get_first_free_ip(self):
        used_ips = set(self.ips.values_list('number', flat=True))
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
        """
        Search networks (ancestors) order first by min_ip descending,
        then by max_ip ascending, to get smallest ancestor network
        containing current network.
        """
        nets = Network.objects.filter(
            min_ip__lte=self.min_ip,
            max_ip__gte=self.max_ip
        ).exclude(pk=self.id).order_by('-min_ip', 'max_ip')
        return nets


class DiscoveryQueue(NamedMixin, models.Model):

    class Meta:
        verbose_name = _('discovery queue')
        verbose_name_plural = _('discovery queues')
        ordering = ('name',)


class IPAddressQuerySet(models.QuerySet):
    def create(self, base_object=None, mac=None, label=None, **kwargs):
        with transaction.atomic():
            eth = kwargs.pop('ethernet', None)
            if base_object and not eth:
                eth = Ethernet.objects.create(
                    base_object=base_object, mac=mac, label=label
                )
            ip = self.model(ethernet=eth, **kwargs)
            ip.save(force_insert=True)
        return ip


class IPAddress(
    AdminAbsoluteUrlMixin,
    LastSeenMixin,
    TimeStampMixin,
    NetworkMixin,
    models.Model
):
    _parent_attr = 'network'

    ethernet = models.OneToOneField(
        Ethernet,
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
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
        null=False,
    )
    hostname = NullableCharField(
        verbose_name=_('Hostname'),
        max_length=255,
        null=True,
        blank=True,
        default=None,
        # TODO: unique
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
        verbose_name=_('Is management address'),
        default=False,
    )
    is_public = models.BooleanField(
        verbose_name=_('Is public'),
        default=False,
        editable=False,
    )
    is_gateway = models.BooleanField(
        verbose_name=_('Is gateway'),
        default=False,
    )
    status = models.PositiveSmallIntegerField(
        default=IPAddressStatus.used.id,
        choices=IPAddressStatus(),
    )
    dhcp_expose = models.BooleanField(
        default=False,
        verbose_name=_('Expose in DHCP'),
    )
    objects = IPAddressQuerySet.as_manager()

    class Meta:
        verbose_name = _('IP address')
        verbose_name_plural = _('IP addresses')

    def __str__(self):
        return self.address

    def _validate_expose_in_dhcp_and_mac(self):
        if (
            (not self.ethernet_id or (self.ethernet and not self.ethernet.mac)) and  # noqa
            self.dhcp_expose
        ):
            raise ValidationError({
                'dhcp_expose': (
                    'Cannot expose in DHCP without MAC address'
                )
            })

    def _validate_expose_in_dhcp_and_hostname(self):
        if not self.hostname and self.dhcp_expose:
            raise ValidationError({
                'hostname': (
                    'Cannot expose in DHCP without hostname'
                )
            })

    def _validate_change_when_exposing_in_dhcp(self):
        """
        Check if one of hostname, address or ethernet is changed
        when entry is exposed in DHCP.
        """
        if self.pk and settings.DHCP_ENTRY_FORBID_CHANGE:
            old_obj = self.__class__._default_manager.get(pk=self.pk)
            if old_obj.dhcp_expose:
                for attr_name, field_name in [
                    ('hostname', 'hostname'),
                    ('address', 'address'),
                    ('ethernet_id', 'ethernet'),
                ]:
                    if getattr(old_obj, attr_name) != getattr(self, attr_name):
                        raise ValidationError(
                            'Cannot change {} when exposing in DHCP'.format(
                                field_name
                            )
                        )

    def clean(self):
        errors = {}
        for validator in [
            super().clean,
            self._validate_expose_in_dhcp_and_mac,
            self._validate_expose_in_dhcp_and_hostname,
            self._validate_change_when_exposing_in_dhcp,
        ]:
            try:
                validator()
            except ValidationError as e:
                e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)

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
            self.number = int(ipaddress.ip_address(self.address or 0))
        self._assign_parent()
        self.is_public = not self.ip.is_private
        # TODO: if not reserved, check for ethernet
        super(IPAddress, self).save(*args, **kwargs)

    @property
    def ip(self):
        return ipaddress.ip_address(self.address)

    @property
    def base_object(self):
        if not self.ethernet:
            return None
        return self.ethernet.base_object

    @base_object.setter
    def base_object(self, value):
        if self.ethernet:
            self.ethernet.base_object = value
            self.ethernet.save()
        else:
            eth = Ethernet.objects.create(base_object=value)
            self.ethernet = eth
            self.save()

    def search_networks(self):
        """
        Search networks (ancestors) order first by min_ip descending,
        then by max_ip ascending, to get smallest ancestor network
        containing current network.
        """
        int_value = int(self.ip)
        nets = Network.objects.filter(
            min_ip__lte=int_value,
            max_ip__gte=int_value
        ).order_by('-min_ip', 'max_ip')
        return nets


@receiver(post_migrate)
def rebuild_handler(sender, **kwargs):
    """
    Rebuild Network tree after migration of operations app.
    """
    # post_migrate is called after each app's migrations
    if sender.name == 'ralph.' + Network._meta.app_label:
        Network.objects.rebuild()
