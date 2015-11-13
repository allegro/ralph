# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import Component
from ralph.lib.mixins.models import NamedMixin


class CloudProvider(NamedMixin):
    class Meta:
        verbose_name = _('Cloud provider')
        verbose_name_plural = _('Cloud providers')


class CloudFlavor(BaseObject):
    name = models.CharField(_('name'), max_length=255, unique=True)
    cloudprovider = models.ForeignKey(CloudProvider)
    flavor_id = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return format(self.name)

    @property
    def cores(self):
        """Number of cores"""
        return self.virtualcomponent.filter(
            model__type=ComponentType.processor
        ).values_list('model__cores', flat=True).first()

    @property
    def memory(self):
        """RAM memory size in MiB"""
        return self.virtualcomponent.filter(
            model__type=ComponentType.memory
        ).values_list('model__size', flat=True).first()

    @property
    def disk(self):
        """Disk size in MiB"""
        return self.virtualcomponent.filter(
            model__type=ComponentType.disk
        ).values_list('model__size', flat=True).first()


class CloudProject(BaseObject):
    cloudprovider = models.ForeignKey(CloudProvider)
    project_id = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return 'Cloud Project: {}'.format(self.name)


@receiver(models.signals.post_save, sender=CloudProject)
def update_service_env_on_cloudproject_save(sender, instance, **kwargs):
    """Update CloudHost service_env while updating CloudProject"""
    # import ipdb; ipdb.set_trace()
    if instance.pk is not None:
        old = sender.objects.get(pk=instance.pk)
        for host in old.children.all():
            if host.service_env != instance.service_env:
                # TODO: save nie dziala z admina
                host.service_env = instance.service_env
                host.save()
            # with transaction.atomic(), revisions.create_revision():
            #   host.save()
            #   revisions.set_comment('Project service_env updated')


class CloudHost(BaseObject):
    host_id = models.CharField(unique=True, max_length=100)
    hostname = models.CharField(max_length=100)
    cloudflavor = models.ForeignKey(CloudFlavor, verbose_name='Instance Type')

    class Meta:
        verbose_name = _('Cloud host')
        verbose_name_plural = _('Cloud hosts')

    def __str__(self):
        return 'Cloud Host: {}'.format(self.hostname)

    @property
    def ip_addresses(self):
        return ','.join(self.ipaddress_set.values_list('address', flat=True))


@receiver(models.signals.pre_save, sender=CloudHost)
def inherit_service_env_on_cloudhost_add(sender, instance, **kwargs):
    """Set service_env to parent(CloudProject).service_env when adding new
    CloudHost"""
    if not instance.pk:
        instance.service_env = instance.parent.service_env


class VirtualComponent(Component):
    pass


class VirtualServer(BaseObject):
    # TODO This model has to be developed, eg. add hostanme, hypervisior e.t.c.
    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')

    def __str__(self):
        return 'VirtualServer: {}'.format(self.service_env)
