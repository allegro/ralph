from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ralph.data_center.models import DataCenterAsset
from ralph.deployment.models import Deployment
from ralph.networks.models.networks import IPAddress, IPAddressStatus


class DHCPEntryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'ethernet', 'ethernet__base_object'
        ).exclude(
            hostname=None,
            ethernet__base_object=None,
            ethernet=None,
            status=IPAddressStatus.reserved.id
        )

    # TODO: delete this
    def entries(self, networks):
        queryset = self.get_queryset().filter(network__in=networks)
        deployment_queryset = Deployment.objects.active()
        entries_ids = queryset.values_list(
            'ethernet__base_object_id', flat=True
        )
        dca_content_type = ContentType.objects.get_for_model(DataCenterAsset)
        deployment_ids = deployment_queryset.filter(
            object_id__in=[str(i) for i in entries_ids],
            content_type=dca_content_type
        )
        deployments_mapper = {
            obj.object_id: obj
            for obj in Deployment.objects.filter(
                id__in=deployment_ids
            )
        }
        for obj in queryset:
            obj.deployment = deployments_mapper.get(
                str(obj.ethernet.base_object_id), None
            )
            yield obj


class DHCPEntry(IPAddress):
    objects = DHCPEntryManager()

    @property
    def mac(self):
        return self.ethernet and self.ethernet.mac

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
