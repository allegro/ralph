from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin
from ralph.networks.models.networks import IPAddress, NetworkEnvironment


class DHCPEntryManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("ethernet", "ethernet__base_object")
            .filter(
                hostname__isnull=False,
                dhcp_expose=True,
                ethernet__base_object__isnull=False,
                ethernet__isnull=False,
                ethernet__mac__isnull=False,
            )
        )


class DHCPEntry(IPAddress):
    objects = DHCPEntryManager()

    @property
    def mac(self):
        return self.ethernet and self.ethernet.mac

    class Meta:
        proxy = True


class DHCPServer(AdminAbsoluteUrlMixin, models.Model):
    ip = models.GenericIPAddressField(verbose_name=_("IP address"), unique=True)
    network_environment = models.ForeignKey(
        NetworkEnvironment, null=True, blank=True, on_delete=models.CASCADE
    )
    last_synchronized = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("DHCP Server")
        verbose_name_plural = _("DHCP Servers")

    @classmethod
    def update_last_synchronized(cls, ip, time=None):
        if not time:
            time = timezone.now()
        return cls.objects.filter(ip=ip).update(last_synchronized=time)


class DNSServerGroup(NamedMixin, AdminAbsoluteUrlMixin, models.Model):
    servers = models.ManyToManyField("DNSServer", through="DNSServerGroupOrder")

    class Meta:
        verbose_name = _("DNS Server Group")
        verbose_name_plural = _("DNS Server Groups")

    def __str__(self):
        servers = (
            DNSServerGroupOrder.objects.select_related("dns_server")
            .filter(dns_server_group=self)
            .values_list("dns_server__ip_address", flat=True)
        )
        return "{} ({})".format(self.name, ", ".join(servers))


class DNSServerGroupOrder(models.Model):
    dns_server_group = models.ForeignKey(
        "DNSServerGroup", related_name="server_group_order", on_delete=models.CASCADE
    )
    dns_server = models.ForeignKey(
        "DNSServer", related_name="server_group_order", on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(editable=True, db_index=True)

    class Meta:
        unique_together = (("dns_server_group", "dns_server"),)
        ordering = ("order",)

    def __str__(self):
        return self.dns_server.ip_address


class DNSServer(AdminAbsoluteUrlMixin, models.Model):
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP address"),
        unique=True,
    )

    class Meta:
        verbose_name = _("DNS Server")
        verbose_name_plural = _("DNS Servers")

    def __str__(self):
        return self.ip_address
