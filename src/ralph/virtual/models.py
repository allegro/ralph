# -*- coding: utf-8 -*-
import logging

from dj.choices import Choices
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.admin.helpers import get_value_by_relation_path
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import Component, ComponentModel, Ethernet
from ralph.assets.utils import DNSaaSPublisherMixin
from ralph.data_center.models.physical import (
    DataCenterAsset,
    NetworkableBaseObject
)
from ralph.data_center.models.virtual import Cluster
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.transitions.fields import TransitionField
from ralph.networks.models.networks import IPAddress

logger = logging.getLogger(__name__)


class CloudProvider(AdminAbsoluteUrlMixin, NamedMixin):
    class Meta:
        verbose_name = _('Cloud provider')
        verbose_name_plural = _('Cloud providers')


class CloudFlavor(AdminAbsoluteUrlMixin, BaseObject):
    name = models.CharField(_('name'), max_length=255)
    cloudprovider = models.ForeignKey(CloudProvider)
    cloudprovider._autocomplete = False

    flavor_id = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name

    def _set_component(self, model_args):
        """ create/modify component cpu, mem or disk"""
        try:
            model = ComponentModel.objects.get(name=model_args['name'])
        except ObjectDoesNotExist:
            model = ComponentModel()
            for key, value in model_args.items():
                setattr(model, key, value)
            model.save()
        try:
            VirtualComponent.objects.get(base_object=self, model=model)
        except ObjectDoesNotExist:
            for component in self.virtualcomponent_set.filter(
                model__type=model_args['type']
            ):
                component.delete()

            VirtualComponent(base_object=self, model=model).save()

    def _get_component(self, model_type, field_path):
        # use cached components if already prefetched (using prefetch_related)
        # otherwise, perform regular SQL query
        try:
            components = self._prefetched_objects_cache['virtualcomponent']
        except (KeyError, AttributeError):
            return self.virtualcomponent_set.filter(
                model__type=model_type
            ).values_list(field_path, flat=True).first()
        else:
            for component in components:
                if component.model.type == model_type:
                    return get_value_by_relation_path(component, field_path)
            return None

    @property
    def cores(self):
        """Number of cores"""
        return self._get_component(ComponentType.processor, 'model__cores')

    @cores.setter
    def cores(self, new_cores):
        cpu = {
            'name': "{} cores vCPU".format(new_cores),
            'cores': new_cores,
            'family': 'vcpu',
            'type': ComponentType.processor
        }
        if self.cores != new_cores:
            self._set_component(cpu)

    @property
    def memory(self):
        """RAM memory size in MiB"""
        return self._get_component(ComponentType.memory, 'model__size')

    @memory.setter
    def memory(self, new_memory):
        ram = {
            'name': "{} MiB vMEM".format(new_memory),
            'size': new_memory,
            'type': ComponentType.memory,
        }
        if self.memory != new_memory:
            self._set_component(ram)

    @property
    def disk(self):
        """Disk size in MiB"""
        return self._get_component(ComponentType.disk, 'model__size')

    @disk.setter
    def disk(self, new_disk):
        disk = {
            'name': "{} GiB vHDD".format(int(new_disk / 1024)),
            'size': new_disk,
            'type': ComponentType.disk,
        }
        if self.disk != new_disk:
            self._set_component(disk)


class CloudProject(AdminAbsoluteUrlMixin, BaseObject):
    cloudprovider = models.ForeignKey(CloudProvider)
    cloudprovider._autocomplete = False

    project_id = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return 'Cloud Project: {}'.format(self.name)


@receiver(models.signals.post_save, sender=CloudProject)
def update_service_env_on_cloudproject_save(sender, instance, **kwargs):
    """Update CloudHost service_env while updating CloudProject"""
    if instance.pk is not None:
        instance.children.all().update(service_env=instance.service_env)


class CloudHost(AdminAbsoluteUrlMixin, BaseObject):
    def save(self, *args, **kwargs):
        try:
            self.service_env = self.parent.service_env
        except AttributeError:
            pass
        super(CloudHost, self).save(*args, **kwargs)

    cloudflavor = models.ForeignKey(CloudFlavor, verbose_name='Instance Type')
    cloudprovider = models.ForeignKey(CloudProvider)
    cloudprovider._autocomplete = False

    host_id = models.CharField(unique=True, max_length=100)
    hostname = models.CharField(max_length=100)
    hypervisor = models.ForeignKey(DataCenterAsset, blank=True, null=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('Cloud host')
        verbose_name_plural = _('Cloud hosts')

    def __str__(self):
        return self.hostname

    @property
    def ip_addresses(self):
        return self.ethernet_set.select_related('ipaddress').values_list(
            'ipaddress__address', flat=True
        )

    @ip_addresses.setter
    def ip_addresses(self, value):
        if set(self.ip_addresses) == set(value):
            return
        for ip in set(value) - set(self.ip_addresses):
            try:
                new_ip = IPAddress.objects.get(address=ip)
                if new_ip.base_object is None:
                    new_ip.base_object = self
                    new_ip.save()
                else:
                    logger.warning((
                        'Cannot assign IP %s to %s - it is already in use by '
                        'another asset'
                    ) % (ip, self.hostname))
            except ObjectDoesNotExist:
                new_ip = IPAddress(
                    ethernet=Ethernet.objects.create(base_object=self),
                    address=ip
                )
                new_ip.save()

        to_delete = set(self.ip_addresses) - set(value)
        Ethernet.objects.filter(
            base_object=self, ipaddress__address__in=to_delete
        ).delete()

    @property
    def cloudproject(self):
        """Workaround, because parent resolves to BaseObject in rest api"""
        try:
            return self.parent.cloudproject
        except AttributeError:
            return None

    def get_location(self):
        location = []
        if self.hypervisor_id:
            location = self.hypervisor.get_location()
            if self.hypervisor.hostname:
                location.append(self.hypervisor.hostname)
        return location


class VirtualComponent(Component):
    pass


class VirtualServerType(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model
):
    pass


class VirtualServerStatus(Choices):
    _ = Choices.Choice

    new = _('new')
    used = _('in use')
    to_deploy = _('to deploy')
    liquidated = _('liquidated')


class VirtualServer(
    DNSaaSPublisherMixin,
    AdminAbsoluteUrlMixin,
    NetworkableBaseObject,
    BaseObject
):
    # parent field for VirtualServer is hypervisor!
    # TODO: limit parent to DataCenterAsset and CloudHost
    status = TransitionField(
        default=VirtualServerStatus.new.id,
        choices=VirtualServerStatus(),
    )
    type = models.ForeignKey(VirtualServerType, related_name='virtual_servers')
    hostname = NullableCharField(
        blank=True,
        default=None,
        max_length=255,
        null=True,
        verbose_name=_('hostname'),
        unique=True,
    )
    sn = NullableCharField(
        max_length=200,
        verbose_name=_('SN'),
        blank=True,
        default=None,
        null=True,
        unique=True,
    )
    # TODO: remove this field
    cluster = models.ForeignKey(Cluster, blank=True, null=True)

    @cached_property
    def polymorphic_parent(self):
        return self.parent.last_descendant if self.parent_id else None

    def get_location(self):
        if (
            self.parent_id and
            self.parent.content_type_id == ContentType.objects.get_for_model(
                DataCenterAsset
            ).id
        ):
            parent = self.parent.asset.datacenterasset
            location = parent.get_location()
            if parent.hostname:
                location.append(parent.hostname)
        else:
            location = []
        return location

    @property
    def model(self):
        return (
            self.polymorphic_parent.model if self.polymorphic_parent else None
        )

    @cached_property
    def rack_id(self):
        return self.rack.id if self.rack else None

    @cached_property
    def rack(self):
        if self.parent_id:
            polymorphic_parent = self.polymorphic_parent.last_descendant
            if isinstance(polymorphic_parent, DataCenterAsset):
                return polymorphic_parent.rack
        return None

    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')

    def __str__(self):
        return 'VirtualServer: {} ({})'.format(self.hostname, self.sn)


if settings.HERMES_HOST_UPDATE_TOPIC_NAME:
    from ralph.data_center.publishers import publish_host_update

    @receiver(models.signals.post_save, sender=CloudHost)
    def post_save_cloud_host(sender, instance, **kwargs):
        # temporary, until Ralph2 sync is turned on
        # see ralph.ralph2_sync.admin for details
        if getattr(instance, '_handle_post_save', True):
            return publish_host_update(instance)

    @receiver(models.signals.post_save, sender=VirtualServer)
    def post_save_virtual_server(sender, instance, **kwargs):
        # temporary, until Ralph2 sync is turned on
        # see ralph.ralph2_sync.admin for details
        if getattr(instance, '_handle_post_save', True):
            return publish_host_update(instance)
