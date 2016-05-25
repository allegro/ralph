from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ralph.networks.models.networks import IPAddress, IPAddressStatus


class DHCPEntryManager(models.Manager):
    def get_queryset(self):
        # TODO: add deployment id (job id)
        return super().get_queryset().select_related('ethernet').exclude(
            hostname=None,
            ethernet__base_object=None,
            ethernet=None,
            status=IPAddressStatus.reserved.id
        )

    def entries(self, networks):
        qs = self.get_queryset().filter(network__in=networks)
        ids = qs.values_list('id', flat=True)
        import ipdb; ipdb.set_trace()

        return qs

class DHCPEntry(IPAddress):
    # mac = models.CharField(
    #     verbose_name=_('MAC address'), unique=True,
    #     validators=[mac_validator], max_length=24, null=False, blank=False
    # )
    # ip_address = models.GenericIPAddressField(
    #     verbose_name=_('IP address'),
    #     help_text=_('Presented as string.'),
    #     unique=True,
    #     blank=False,
    #     default=None,
    # )
    objects = DHCPEntryManager()

    @property
    def mac(self):
        return self.ethernet and self.ethernet.mac

    @property
    def deployment(self):
        return 1

    class Meta:
        proxy = True


class DHCPServer(models.Model):
    ip = models.GenericIPAddressField(
        verbose_name=_('IP address'), unique=True
    )
    last_synchronized = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('DHCP Server')
        verbose_name_plural = _('DHCP Servers')

    @classmethod
    def update_last_synchronized(cls, ip, time=None):
        if not time:
            time = timezone.now()
        return cls.objects.filter(ip=ip).update(last_synchronized=time)


class DNSServer(models.Model):
    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
        unique=True,
    )
    is_default = models.BooleanField(
        verbose_name=_('is default'),
        db_index=True,
        default=False,
    )

    class Meta:
        verbose_name = _('DNS Server')
        verbose_name_plural = _('DNS Servers')

    def __str__(self):
        return '{}'.format(self.ip_address)
