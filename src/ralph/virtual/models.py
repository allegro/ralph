# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

from dj.choices import Choices
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_cryptography.fields import encrypt
from django_extensions.db.fields.json import JSONField

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
from ralph.data_center.publishers import publish_host_update
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    PreviousStateMixin,
    TimeStampMixin
)
from ralph.lib.transitions.fields import TransitionField
from ralph.networks.models.networks import IPAddress
from ralph.signals import post_commit

logger = logging.getLogger(__name__)


class CloudProvider(AdminAbsoluteUrlMixin, NamedMixin):
    class Meta:
        verbose_name = _("Cloud provider")
        verbose_name_plural = _("Cloud providers")

    cloud_sync_enabled = models.BooleanField(null=False, blank=False, default=False)
    cloud_sync_driver = models.CharField(max_length=128, null=True, blank=True)
    client_config = encrypt(
        JSONField(
            blank=True,
            null=True,
            verbose_name="client configuration",
        )
    )


class CloudFlavor(AdminAbsoluteUrlMixin, BaseObject):
    name = models.CharField(_("name"), max_length=255)
    cloudprovider = models.ForeignKey(CloudProvider, on_delete=models.CASCADE)
    cloudprovider._autocomplete = False

    flavor_id = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name

    def _set_component(self, model_args):
        """create/modify component cpu, mem or disk"""
        try:
            model = ComponentModel.objects.get(name=model_args["name"])
        except ObjectDoesNotExist:
            model = ComponentModel()
            for key, value in model_args.items():
                setattr(model, key, value)
            model.save()
        try:
            VirtualComponent.objects.get(base_object=self, model=model)
        except ObjectDoesNotExist:
            for component in self.virtualcomponent_set.filter(
                model__type=model_args["type"]
            ):
                component.delete()

            VirtualComponent(base_object=self, model=model).save()

    def _get_component(self, model_type, field_path):
        # use cached components if already prefetched (using prefetch_related)
        # otherwise, perform regular SQL query
        try:
            components = self._prefetched_objects_cache["virtualcomponent_set"]
        except (KeyError, AttributeError):
            return (
                self.virtualcomponent_set.filter(model__type=model_type)
                .values_list(field_path, flat=True)
                .first()
            )
        else:
            for component in components:
                if component.model.type == model_type:
                    return get_value_by_relation_path(component, field_path)
            return None

    @property
    def cores(self):
        """Number of cores"""
        return self._get_component(ComponentType.processor, "model__cores")

    @cores.setter
    def cores(self, new_cores):
        cpu = {
            "name": "{} cores vCPU".format(new_cores),
            "cores": new_cores,
            "family": "vcpu",
            "type": ComponentType.processor,
        }
        if self.cores != new_cores:
            self._set_component(cpu)

    @property
    def memory(self):
        """RAM memory size in MiB"""
        return self._get_component(ComponentType.memory, "model__size")

    @memory.setter
    def memory(self, new_memory):
        ram = {
            "name": "{} MiB vMEM".format(new_memory),
            "size": new_memory,
            "type": ComponentType.memory,
        }
        if self.memory != new_memory:
            self._set_component(ram)

    @property
    def disk(self):
        """Disk size in MiB"""
        return self._get_component(ComponentType.disk, "model__size")

    @disk.setter
    def disk(self, new_disk):
        disk = {
            "name": "{} GiB vHDD".format(int(new_disk / 1024)),
            "size": new_disk,
            "type": ComponentType.disk,
        }
        if self.disk != new_disk:
            self._set_component(disk)


class CloudProject(PreviousStateMixin, AdminAbsoluteUrlMixin, BaseObject):
    cloudprovider = models.ForeignKey(CloudProvider, on_delete=models.CASCADE)
    cloudprovider._autocomplete = False
    custom_fields_inheritance = OrderedDict(
        [
            ("service_env", "assets.ServiceEnvironment"),
        ]
    )

    project_id = models.CharField(
        verbose_name=_("project ID"), unique=True, max_length=100
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return "Cloud Project: {}".format(self.name)


class CloudImage(AdminAbsoluteUrlMixin, models.Model):
    image_id = models.CharField(verbose_name=_("image ID"), unique=True, max_length=100)
    name = models.CharField(max_length=200, unique=False)

    def __str__(self):
        return "Cloud Image: {}".format(self.name)


@receiver(models.signals.post_save, sender=CloudProject)
def update_service_env_on_cloudproject_save(sender, instance, **kwargs):
    """Update CloudHost service_env while updating CloudProject"""
    if instance.pk is not None:
        instance.children.all().update(service_env=instance.service_env)


class CloudHost(
    PreviousStateMixin, AdminAbsoluteUrlMixin, NetworkableBaseObject, BaseObject
):
    _allow_in_dashboard = True
    previous_dc_host_update_fields = ["hostname"]
    custom_fields_inheritance = OrderedDict(
        [
            ("parent__cloudproject", "virtual.CloudProject"),
            ("configuration_path", "assets.ConfigurationClass"),
            ("configuration_path__module", "assets.ConfigurationModule"),
            ("service_env", "assets.ServiceEnvironment"),
        ]
    )

    def save(self, *args, **kwargs):
        try:
            self.service_env = self.parent.service_env
        except AttributeError:
            pass
        super(CloudHost, self).save(*args, **kwargs)

    cloudflavor = models.ForeignKey(
        CloudFlavor, verbose_name="Instance Type", on_delete=models.CASCADE
    )
    cloudprovider = models.ForeignKey(CloudProvider, on_delete=models.CASCADE)
    cloudprovider._autocomplete = False

    host_id = models.CharField(verbose_name=_("host ID"), unique=True, max_length=100)
    hostname = models.CharField(verbose_name=_("hostname"), max_length=255)
    hypervisor = models.ForeignKey(
        DataCenterAsset, blank=True, null=True, on_delete=models.CASCADE
    )
    image_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _("Cloud host")
        verbose_name_plural = _("Cloud hosts")

    def __str__(self):
        return self.hostname

    @cached_property
    def rack_id(self):
        return self.rack.id if self.rack else None

    @cached_property
    def rack(self):
        if self.hypervisor:
            return self.hypervisor.rack
        return None

    @property
    def ipaddresses(self):
        # NetworkableBaseObject compatibility
        return IPAddress.objects.filter(ethernet__base_object=self)

    @property
    def ip_addresses(self):
        return self.ethernet_set.select_related("ipaddress").values_list(
            "ipaddress__address", flat=True
        )

    @ip_addresses.setter
    def ip_addresses(self, value):
        # value is a list (of ips) or dict (of ip:hostname pairs)
        # when value is a dict, set will work on keys only
        for ip in set(value) - set(self.ip_addresses):
            try:
                new_ip = IPAddress.objects.get(address=ip)
                if new_ip.base_object is None:
                    new_ip.base_object = self
                    new_ip.save()
                else:
                    logger.warning(
                        "Cannot assign IP %s to %s - it is already in use by "
                        "another asset",
                        ip,
                        self.hostname,
                    )
            except ObjectDoesNotExist:
                logger.info("Creating new IP {} for {}".format(ip, self))
                new_ip = IPAddress(
                    ethernet=Ethernet.objects.create(base_object=self), address=ip
                )
                new_ip.save()
        # refresh hostnames
        if isinstance(value, dict):
            for address, hostname in value.items():
                try:
                    ip = IPAddress.objects.get(address=address)
                except IPAddress.DoesNotExist:
                    logger.debug("IP {} not found".format(address))
                else:
                    if ip.hostname != hostname:
                        logger.info(
                            "Setting {} for IP {} (previous value: {})".format(
                                hostname, address, ip.hostname
                            )
                        )
                        ip.hostname = hostname
                        ip.save()

        to_delete = set(self.ip_addresses) - set(value)
        for ip in to_delete:
            logger.warning("Deleting %s from %s", ip, self)
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
    AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model
):
    pass


class VirtualServerStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    used = _("in use")
    to_deploy = _("to deploy")
    liquidated = _("liquidated")


class VirtualServer(
    PreviousStateMixin,
    DNSaaSPublisherMixin,
    AdminAbsoluteUrlMixin,
    NetworkableBaseObject,
    BaseObject,
):
    # parent field for VirtualServer is hypervisor!
    # TODO: limit parent to DataCenterAsset and CloudHost
    status = TransitionField(
        default=VirtualServerStatus.new.id,
        choices=VirtualServerStatus(),
    )
    type = models.ForeignKey(
        VirtualServerType, related_name="virtual_servers", on_delete=models.CASCADE
    )
    hostname = NullableCharField(
        blank=True,
        default=None,
        max_length=255,
        null=True,
        verbose_name=_("hostname"),
        unique=True,
    )
    sn = NullableCharField(
        max_length=200,
        verbose_name=_("SN"),
        blank=True,
        default=None,
        null=True,
        unique=True,
    )
    # TODO: remove this field
    cluster = models.ForeignKey(
        Cluster, blank=True, null=True, on_delete=models.CASCADE
    )

    previous_dc_host_update_fields = ["hostname"]
    _allow_in_dashboard = True

    @cached_property
    def polymorphic_parent(self):
        return self.parent.last_descendant if self.parent_id else None

    def get_location(self):
        if (
            self.parent_id
            and self.parent.content_type_id
            == ContentType.objects.get_for_model(DataCenterAsset).id
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
        return self.type

    @cached_property
    def rack_id(self):
        return self.rack.id if self.rack else None

    @cached_property
    def rack(self):
        if self.parent_id:
            polymorphic_parent = self.polymorphic_parent.last_descendant
            if isinstance(polymorphic_parent, (DataCenterAsset, CloudHost)):
                return polymorphic_parent.rack
        return None

    class Meta:
        verbose_name = _("Virtual server (VM)")
        verbose_name_plural = _("Virtual servers (VM)")

    def __str__(self):
        return "VirtualServer: {} ({})".format(self.hostname, self.sn)


post_commit(publish_host_update, VirtualServer)
post_commit(publish_host_update, CloudHost)
