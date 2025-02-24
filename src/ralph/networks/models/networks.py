# -*- coding: utf-8 -*-
import ipaddress
import logging
import socket
import struct

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_migrate, pre_save
from django.db.utils import ProgrammingError
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.assets.models import AssetLastHostname, Ethernet
from ralph.dns.dnsaas import DNSaaS
from ralph.lib import network as network_tools
from ralph.lib.mixins.fields import (
    NullableCharField,
    NullableCharFieldWithAutoStrip
)
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    LastSeenMixin,
    NamedMixin,
    PreviousStateMixin,
    TimeStampMixin
)
from ralph.lib.polymorphic.fields import PolymorphicManyToManyField
from ralph.networks.fields import IPNetwork
from ralph.networks.models.choices import IPAddressStatus

logger = logging.getLogger(__name__)


def is_in_dnsaas(ip):
    if not settings.ENABLE_DNSAAS_INTEGRATION:
        return False
    dnsaas_client = DNSaaS()
    url = dnsaas_client.build_url("records", get_params=[("ip", ip), ("type", "A")])
    return len(dnsaas_client.get_api_result(url)) > 0


class NetworkKind(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    class Meta:
        verbose_name = _("network kind")
        verbose_name_plural = _("network kinds")
        ordering = ("name",)


class NetworkEnvironment(
    AdminAbsoluteUrlMixin, TimeStampMixin, NamedMixin, models.Model
):
    data_center = models.ForeignKey(
        "data_center.DataCenter",
        verbose_name=_("data center"),
        on_delete=models.CASCADE,
    )
    queue = models.ForeignKey(
        "DiscoveryQueue",
        verbose_name=_("discovery queue"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    hostname_template_counter_length = models.PositiveIntegerField(
        verbose_name=_("hostname template counter length"),
        default=4,
    )
    hostname_template_prefix = models.CharField(
        verbose_name=_("hostname template prefix"),
        max_length=30,
    )
    hostname_template_postfix = models.CharField(
        verbose_name=_("hostname template postfix"),
        max_length=30,
        help_text=_(
            "This value will be used as a postfix when generating new hostname "
            'in this network environment. For example, when prefix is "s1", '
            'postfix is ".mydc.net" and counter length is 4, following '
            " hostnames will be generated: s10000.mydc.net, s10001.mydc.net, .."
            ", s19999.mydc.net."
        ),
    )
    domain = NullableCharField(
        verbose_name=_("domain"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Used in DHCP configuration."),
    )
    remarks = models.TextField(
        verbose_name=_("remarks"),
        help_text=_("Additional information."),
        blank=True,
        null=True,
    )
    use_hostname_counter = models.BooleanField(
        default=True,
        help_text="If set to false hostname based on already added hostnames.",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)

    @property
    def HOSTNAME_MODELS(self):
        from ralph.data_center.models.physical import DataCenterAsset
        from ralph.data_center.models.virtual import Cluster
        from ralph.virtual.models import VirtualServer

        return (DataCenterAsset, VirtualServer, Cluster, IPAddress)

    @property
    def next_free_hostname(self):
        """
        Retrieve next free hostname
        """
        if self.use_hostname_counter:
            return AssetLastHostname.get_next_free_hostname(
                self.hostname_template_prefix,
                self.hostname_template_postfix,
                self.hostname_template_counter_length,
                self.check_hostname_is_available,
            )
        else:
            result = self.next_hostname_without_model_counter()
        return result

    def check_hostname_is_available(self, hostname):
        if not hostname:
            return False

        for model_class in self.HOSTNAME_MODELS:
            if model_class.objects.filter(hostname=hostname).exists():
                return False

        return True

    def issue_next_free_hostname(self):
        """
        Retrieve and reserve next free hostname
        """
        if self.use_hostname_counter:
            hostname = None

            while not self.check_hostname_is_available(hostname):
                hostname = AssetLastHostname.increment_hostname(
                    self.hostname_template_prefix,
                    self.hostname_template_postfix,
                ).formatted_hostname(self.hostname_template_counter_length)

            return hostname

        return self.next_hostname_without_model_counter()

    def current_counter_without_model(self):
        """
        Return current counter based on already added hostnames

        Returns:
            counter int
        """
        start = len(self.hostname_template_prefix)
        stop = -len(self.hostname_template_postfix)
        hostnames = []
        for model_class in self.HOSTNAME_MODELS:
            item = (
                model_class.objects.filter(
                    hostname__iregex="{}[0-9]+{}".format(
                        self.hostname_template_prefix, self.hostname_template_postfix
                    )
                )
                .order_by("-hostname")
                .first()
            )
            if item and item.hostname:
                hostnames.append(item.hostname[start:stop])
        counter = 0
        if hostnames:
            # queryset guarantees that hostnames are valid number
            # therefore we can skip ValueError
            counter = int(sorted(hostnames, reverse=True)[0])
        return counter

    def next_counter_without_model(self):
        """
        Return next counter based on already added hostnames

        Returns:
            counter int
        """
        return self.current_counter_without_model() + 1

    def next_hostname_without_model_counter(self):
        """
        Return hostname based on already added hostnames

        Returns:
            hostname string
        """
        hostname = AssetLastHostname(
            prefix=self.hostname_template_prefix,
            counter=self.next_counter_without_model(),
            postfix=self.hostname_template_postfix,
        )
        return hostname.formatted_hostname(self.hostname_template_counter_length)


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
    models.Model,
):
    """
    Class for networks.
    """

    _parent_attr = "parent"
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        editable=False,
        on_delete=models.CASCADE,
    )
    address = IPNetwork(
        verbose_name=_("network address"),
        help_text=_("Presented as string (e.g. 192.168.0.0/24)"),
        unique=True,
    )
    address._filter_title = _("Network Class")
    gateway = models.ForeignKey(
        "IPAddress",
        verbose_name=_("Gateway address"),
        null=True,
        blank=True,
        related_name="gateway_network",
        on_delete=models.SET_NULL,
    )
    remarks = models.TextField(
        verbose_name=_("remarks"),
        help_text=_("Additional information."),
        blank=True,
        default="",
    )
    # TODO: create ManyToManyBaseObjectField to avoid through table
    terminators = PolymorphicManyToManyField(
        "assets.BaseObject", verbose_name=_("network terminators"), blank=True
    )
    vlan = models.PositiveIntegerField(
        verbose_name=_("VLAN number"),
        null=True,
        blank=True,
        default=None,
    )
    racks = models.ManyToManyField(
        "data_center.Rack",
        verbose_name=_("racks"),
        blank=True,
    )
    network_environment = models.ForeignKey(
        NetworkEnvironment,
        verbose_name=_("environment"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    network_environment._autocomplete = False
    min_ip = models.DecimalField(
        verbose_name=_("smallest IP number"),
        editable=False,
        max_digits=39,
        decimal_places=0,
    )
    max_ip = models.DecimalField(
        verbose_name=_("largest IP number"),
        editable=False,
        max_digits=39,
        decimal_places=0,
    )
    kind = models.ForeignKey(
        NetworkKind,
        verbose_name=_("network kind"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    dhcp_broadcast = models.BooleanField(
        verbose_name=_("Broadcast in DHCP configuration"),
        default=True,
        db_index=True,
    )
    service_env = models.ForeignKey(
        "assets.ServiceEnvironment",
        related_name="networks",
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
    )
    dns_servers_group = models.ForeignKey(
        "dhcp.DNSServerGroup",
        null=True,
        blank=True,
        related_name="networks",
        on_delete=models.PROTECT,
    )
    reserved_from_beginning = models.PositiveIntegerField(
        help_text=_(
            "Number of addresses to be omitted in DHCP automatic assignment"
            "counted from the first IP in range (excluding network address)"
        ),
        default=settings.DEFAULT_NETWORK_BOTTOM_MARGIN,
    )
    reserved_from_end = models.PositiveIntegerField(
        help_text=_(
            "Number of addresses to be omitted in DHCP automatic assignment"
            "counted from the last IP in range (excluding broadcast address)"
        ),
        default=settings.DEFAULT_NETWORK_TOP_MARGIN,
    )

    @property
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
            struct.pack(">I", (0xFFFFFFFF << (32 - self.netmask)) & 0xFFFFFFFF)
        )

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

    @property
    def _has_address_changed(self):
        return self.address != self._old_address

    @property
    def reserved_bottom(self):
        # DEPRECATED
        return self.reserved_from_beginning

    @property
    def reserved_top(self):
        # DEPRECATED
        return self.reserved_from_end

    class Meta:
        verbose_name = _("network")
        verbose_name_plural = _("networks")
        unique_together = ("min_ip", "max_ip")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_address = self.address

    def __str__(self):
        return "{} ({} | VLAN: {})".format(self.name, self.address, self.vlan)

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
        # TODO: gateway status? reserved? or maybe regular ip field instead of
        # PK?
        if self.gateway_id and not self.gateway.is_gateway:
            self.gateway.is_gateway = True
            self.gateway.status = IPAddressStatus.reserved
            self.gateway.save()

        update_subnetworks_parent = kwargs.pop("update_subnetworks_parent", True)
        creating = not self.pk
        # store previous subnetworks to update them when address has changed
        if self._has_address_changed and update_subnetworks_parent and not creating:
            prev_subnetworks = self.get_immediate_subnetworks()
        else:
            prev_subnetworks = []

        self.min_ip = int(self.network_address)
        self.max_ip = int(self.broadcast_address)
        self._assign_parent()
        super(Network, self).save(*args, **kwargs)

        # change related ips and (sub)networks only if address has changed
        if self._has_address_changed or creating:
            # after changing address, assign new ips to this network
            self._assign_new_ips_to_network()
            # change also ip addresses which are no longer in scope of current
            # network
            self._unassign_ips_from_network()
            if update_subnetworks_parent:
                self._update_subnetworks_parent(prev_subnetworks)

    def delete(self):
        # Save fake address so that all children of network changed its
        # parent, only then network is removed.
        with transaction.atomic():
            self.address = "0.0.0.0/32"
            self.save()
            super().delete()

    def _update_subnetworks_parent(self, prev_subnetworks):
        """
        When address change, update information about parent in previous and
        current subnetworks.
        """
        # re-save previous subnetworks
        for network in prev_subnetworks:
            network.save(update_subnetworks_parent=False)
        # re-save current subnetworks
        for network in self.get_immediate_subnetworks():
            network.save(update_subnetworks_parent=False)
        # current network is intermediate network between previous parent and
        # previous child - re-save child to assign current network as a parent
        # example:
        # previous state:
        # * netX: 10.20.30.0/24 (parent)
        # * netY: 10.20.30.240/28 (child)
        # adding new network netZ 10.20.30.128/25
        # -> should change parent of netY to netZ
        for network in self.__class__._default_manager.filter(
            parent=self.parent, min_ip__gte=self.min_ip, max_ip__lte=self.max_ip
        ):
            network.save(update_subnetworks_parent=False)

    def _assign_new_ips_to_network(self):
        """
        Filter IP addresses in scope of this network and save them, to
        (possibly) assign them to current network (according to rules in
        IPAddress.save)
        """
        for ip in (
            IPAddress.objects.exclude(
                network=self,
            )
            .exclude(network__in=self.get_subnetworks())
            .filter(number__gte=self.min_ip, number__lte=self.max_ip)
        ):
            # call save instead of update - ip might be assigned to another
            # (smaller) network, which became subnetwork of current network
            ip.save()

    def _unassign_ips_from_network(self):
        """
        Filter IPAddresses which are assigned to current network, but should
        NOT be (their address is not in scope of current network) and save them
        (to reassign them to another network).
        """
        for ip in IPAddress.objects.filter(
            network=self, number__lt=self.min_ip, number__gt=self.max_ip
        ):
            ip.save()

    def get_subnetworks(self):
        return self.get_descendants()

    def get_immediate_subnetworks(self):
        return self.get_children()

    def get_first_free_ip(self):
        used_ips = set(
            IPAddress.objects.filter(
                number__range=(self.min_ip, self.max_ip)
            ).values_list("number", flat=True)
        )
        # add one to omit network address
        min_ip = int(self.min_ip + 1 + self.reserved_from_beginning)
        # subtract 1 to omit broadcast address
        max_ip = int(self.max_ip - 1 - self.reserved_from_end)
        free_ip_as_int = None
        for free_ip_as_int in range(min_ip, max_ip + 1):
            if free_ip_as_int not in used_ips:
                next_free_ip = ipaddress.ip_address(free_ip_as_int)
                if is_in_dnsaas(next_free_ip):
                    logger.warning("IP %s is already in DNS", next_free_ip)
                else:
                    return next_free_ip

    def issue_next_free_ip(self):
        # TODO: exception when any free IP found
        ip_address = self.get_first_free_ip()
        return IPAddress.objects.create(address=str(ip_address))

    def search_networks(self):
        """
        Search networks (ancestors) order first by min_ip descending,
        then by max_ip ascending, to get smallest ancestor network
        containing current network.
        """
        nets = (
            Network.objects.filter(min_ip__lte=self.min_ip, max_ip__gte=self.max_ip)
            .exclude(pk=self.id)
            .order_by("-min_ip", "max_ip")
        )
        return nets


# TODO: remove
class DiscoveryQueue(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    class Meta:
        verbose_name = _("discovery queue")
        verbose_name_plural = _("discovery queues")
        ordering = ("name",)


class IPAddressQuerySet(models.QuerySet):
    def create(self, base_object=None, mac=None, label=None, **kwargs):
        with transaction.atomic():
            eth = kwargs.pop("ethernet", None)
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
    PreviousStateMixin,
    NetworkMixin,
    models.Model,
):
    _parent_attr = "network"

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
        related_name="ips",
        on_delete=models.SET_NULL,
    )
    address = models.GenericIPAddressField(
        verbose_name=_("IP address"),
        help_text=_("Presented as string."),
        unique=True,
        blank=False,
        null=False,
    )
    hostname = NullableCharFieldWithAutoStrip(
        verbose_name=_("hostname"),
        max_length=255,
        null=True,
        blank=True,
        default=None,
        # TODO: unique
    )
    number = models.DecimalField(
        verbose_name=_("IP address"),
        help_text=_("Presented as int."),
        editable=False,
        unique=True,
        max_digits=39,
        decimal_places=0,
        default=None,
    )
    is_management = models.BooleanField(
        verbose_name=_("Is management address"),
        default=False,
    )
    is_public = models.BooleanField(
        verbose_name=_("Is public"),
        default=False,
        editable=False,
    )
    is_gateway = models.BooleanField(
        verbose_name=_("Is gateway"),
        default=False,
    )
    status = models.PositiveSmallIntegerField(
        default=IPAddressStatus.used.id,
        choices=IPAddressStatus(),
    )
    dhcp_expose = models.BooleanField(
        default=False,
        verbose_name=_("Expose in DHCP"),
    )

    class Meta:
        verbose_name = _("IP address")
        verbose_name_plural = _("IP addresses")

    objects = IPAddressQuerySet.as_manager()

    def __str__(self):
        return self.address

    def _hostname_is_unique_in_dc(self, hostname, dc):
        from ralph.dhcp.models import DHCPEntry

        entries_with_hostname = DHCPEntry.objects.filter(
            hostname=hostname, network__network_environment__data_center=dc
        )
        if self.pk:
            entries_with_hostname = entries_with_hostname.exclude(pk=self.pk)
        return not entries_with_hostname.exists()

    def validate_hostname_uniqueness_in_dc(self, hostname):
        network = self.get_network()
        if network and network.network_environment:
            dc = network.network_environment.data_center
            if not self._hostname_is_unique_in_dc(hostname, dc):
                raise ValidationError(
                    'Hostname "{hostname}" is already exposed in DHCP in {dc}.'.format(
                        hostname=self.hostname, dc=dc
                    )
                )

    def _validate_hostname_uniqueness_in_dc(self):
        if not self.dhcp_expose:
            return
        self.validate_hostname_uniqueness_in_dc(self.hostname)

    def _validate_expose_in_dhcp_and_mac(self):
        if (
            (not self.ethernet_id or (self.ethernet and not self.ethernet.mac))  # noqa
            and self.dhcp_expose
        ):
            raise ValidationError(
                {"dhcp_expose": ("Cannot expose in DHCP without MAC address")}
            )

    def _validate_expose_in_dhcp_and_hostname(self):
        if not self.hostname and self.dhcp_expose:
            raise ValidationError(
                {"hostname": ("Cannot expose in DHCP without hostname")}
            )

    def _validate_change_when_exposing_in_dhcp(self):
        """
        Check if one of hostname, address or ethernet is changed
        when entry is exposed in DHCP.
        """
        if self.pk and settings.DHCP_ENTRY_FORBID_CHANGE:
            old_obj = self.__class__._default_manager.get(pk=self.pk)
            if old_obj.dhcp_expose:
                for attr_name, field_name in [
                    ("hostname", "hostname"),
                    ("address", "address"),
                    ("ethernet_id", "ethernet"),
                ]:
                    if getattr(old_obj, attr_name) != getattr(self, attr_name):
                        raise ValidationError(
                            "Cannot change {} when exposing in DHCP".format(field_name)
                        )

    def clean(self):
        errors = {}
        for validator in [
            super().clean,
            self._validate_expose_in_dhcp_and_mac,
            self._validate_expose_in_dhcp_and_hostname,
            self._validate_change_when_exposing_in_dhcp,
            self._validate_hostname_uniqueness_in_dc,
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
                self.address = network_tools.hostname(self.hostname, reverse=True)
            if not self.hostname and self.address:
                self.hostname = network_tools.hostname(self.address)
        if self.number and not self.address:
            self.address = ipaddress.ip_address(int(self.number))
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
            min_ip__lte=int_value, max_ip__gte=int_value
        ).order_by("-min_ip", "max_ip")
        return nets


@receiver(post_migrate)
def rebuild_handler(sender, **kwargs):
    """
    Rebuild Network tree after migration of operations app.
    """
    # post_migrate is called after each app's migrations
    if sender.name == "ralph." + Network._meta.app_label:
        try:
            Network.objects.rebuild()
        except ProgrammingError:
            # this may happen during unapplying initial migration for networks
            # app
            logger.warning("ProgrammingError during Network rebuilding")


@receiver(pre_save, sender=NetworkEnvironment)
def update_counter(sender, instance, **kwargs):
    if not instance.id:
        return

    orig = NetworkEnvironment.objects.get(id=instance.id)
    if instance.use_hostname_counter and not orig.use_hostname_counter:
        obj, created = AssetLastHostname.objects.update_or_create(
            prefix=instance.hostname_template_prefix,
            postfix=instance.hostname_template_postfix,
            defaults={
                "counter": instance.current_counter_without_model(),
            },
        )
