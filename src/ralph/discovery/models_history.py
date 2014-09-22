#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""History models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.db import models as db
from django.db.models.signals import (post_save, pre_save, pre_delete,
                                      post_delete)
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ralph.discovery.models_device import (
    Device,
    DeprecationKind,
    DeviceModel,
)
from ralph.discovery.models_device import LoadBalancerMember
from ralph.discovery.models_device import LoadBalancerVirtualServer
from ralph.discovery.models_component import (
    ComponentModel,
    DiskShare,
    DiskShareMount,
    Ethernet,
    FibreChannel,
    GenericComponent,
    Memory,
    OperatingSystem,
    Processor,
    Software,
    Storage,
)
from ralph.discovery.models_network import IPAddress
from ralph.dnsedit.util import update_txt_records
from ralph.discovery.history import field_changes as _field_changes

FOREVER = '2199-1-1'  # not all DB backends will accept '9999-1-1'
ALWAYS = '0001-1-1'  # not all DB backends will accept '0000-0-0'
SPLUNK_HOST = settings.SPLUNK_LOGGER_HOST


class HistoryChange(db.Model):

    """Represent a single change of a device or one of its components."""

    date = db.DateTimeField(verbose_name=_("date"), default=datetime.now)
    device = db.ForeignKey('Device', verbose_name=_("device"), null=True,
                           blank=True, default=None, on_delete=db.SET_NULL)
    user = db.ForeignKey('auth.User', verbose_name=_("user"), null=True,
                         blank=True, default=None, on_delete=db.SET_NULL)
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')
    component = db.CharField(max_length=255, default='')
    component_id = db.IntegerField(default=None, null=True, blank=True)
    comment = db.TextField(null=True)
    plugin = db.CharField(max_length=64, default='')

    class Meta:
        verbose_name = _("history change")
        verbose_name_plural = _("history changes")

    def __unicode__(self):
        if self.component:
            return "'{}'.'{} ({})'.{} = '{}' -> '{}' by {} on {} ({})".format(
                self.device, self.component, self.component_id,
                self.field_name, self.old_value, self.new_value, self.user,
                self.date, self.id)
        else:
            return "'{}'.{} = '{}' -> '{}' by {} on {} ({})".format(
                self.device, self.field_name, self.old_value, self.new_value,
                self.user, self.date, self.id)


@receiver(post_save, sender=Device, dispatch_uid='ralph.history')
def device_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries when a device changes."""
    dirty = set()
    for field, orig, new in _field_changes(instance, ignore={
            'last_seen', 'cached_cost', 'cached_price', 'raw',
            'uptime_seconds', 'uptime_timestamp'}):
        dirty.add(field)
        HistoryChange(
            device=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
            comment=instance.save_comment,
            plugin=instance.saving_plugin,
        ).save()
    if {'venture', 'venture_role', 'position', 'chassis_position',
            'parent', 'model'} & dirty:
        update_txt_records(instance)


@receiver(pre_delete, sender=Device, dispatch_uid='ralph.history')
def device_pre_delete(sender, instance, using, **kwargs):
    """
    A hook for creating ``HistoryChange`` entries when a device is removed.
    """

    instance.being_deleted = True
    HistoryChange(
        device=None,
        component=unicode(instance),
        field_name='',
        old_value=unicode(instance),
        new_value='',
        user=instance.saving_user,
        plugin=instance.saving_plugin,
    ).save()
    for ip in instance.ipaddress_set.all():
        HistoryChange(
            device=None,
            field_name='device',
            component=unicode(ip),
            component_id=ip.id,
            old_value=unicode(instance),
            new_value='None',
            user=instance.saving_user,
            plugin=instance.saving_plugin,
        ).save()


@receiver(post_save, sender=IPAddress, dispatch_uid='ralph.history.dns')
def device_ipaddress_post_save(sender, instance, raw, using, **kwargs):
    """A hook for updating DNS TXT records when ipaddress is changed."""
    if instance.device:
        update_txt_records(instance.device)
    if instance.dirty_fields.get('device'):
        update_txt_records(instance.dirty_fields.get('device'))


@receiver(post_delete, sender=IPAddress, dispatch_uid='ralph.history.dns')
def device_related_post_delete(sender, instance, using, **kwargs):
    """A hook for updating DNS TXT records when ipaddress is deleted."""
    if instance.device:
        update_txt_records(instance.device)


@receiver(pre_save, sender=Memory, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Processor, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Storage, dispatch_uid='ralph.history')
@receiver(pre_save, sender=DiskShareMount, dispatch_uid='ralph.history')
@receiver(pre_save, sender=DiskShare, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Software, dispatch_uid='ralph.history')
@receiver(pre_save, sender=GenericComponent, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Ethernet, dispatch_uid='ralph.history')
@receiver(pre_save, sender=FibreChannel, dispatch_uid='ralph.history')
@receiver(pre_save, sender=OperatingSystem, dispatch_uid='ralph.history')
@receiver(pre_save, sender=IPAddress, dispatch_uid='ralph.history')
@receiver(pre_save, sender=LoadBalancerMember, dispatch_uid='ralph.history')
@receiver(pre_save, sender=LoadBalancerVirtualServer,
          dispatch_uid='ralph.history')
def device_related_pre_save(sender, instance, raw, using, **kwargs):
    """
    A hook for creating ``HistoryChange`` entry when a component is changed.
    """

    try:
        device = instance.device
    except Device.DoesNotExist:
        device = None
    ignore = {
        'dns_info',
        'hostname',
        'last_puppet',
        'last_seen',
        'network_id',
        'number',
        'snmp_community',
    }
    for field, orig, new in _field_changes(instance, ignore=ignore):
        HistoryChange(
            device=device,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=device.saving_user if device else None,
            component=unicode(instance),
            component_id=instance.id,
            plugin=device.saving_plugin if device else '',
        ).save()


@receiver(pre_delete, sender=Memory, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=Processor, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=Storage, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=DiskShareMount, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=DiskShare, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=Software, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=GenericComponent, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=Ethernet, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=FibreChannel, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=OperatingSystem, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=IPAddress, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=LoadBalancerMember, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=LoadBalancerVirtualServer,
          dispatch_uid='ralph.history')
def device_related_pre_delete(sender, instance, using, **kwargs):
    """
    A hook for creating ``HistoryChange`` entry when a component is deleted.
    """

    HistoryChange(
        device=None,
        field_name='',
        old_value=unicode(instance.device),
        new_value='None',
        component=unicode(instance),
        component_id=instance.id,
        plugin=instance.device.saving_plugin if instance.device else '',
    ).save()


@receiver(pre_save, sender=DeprecationKind, dispatch_uid='ralph.history')
def deprecationkind_pre_save(sender, instance, raw, using, **kwargs):
    if instance.default:
        items = DeprecationKind.objects.filter(default=True)
        for item in items:
            item.default = False
            item.save()


class HistoryModelChange(db.Model):

    """
    Represent a single change in the device and component models.
    """

    date = db.DateTimeField(verbose_name=_("date"), default=datetime.now)
    device_model = db.ForeignKey('DeviceModel', verbose_name=_("device model"),
                                 null=True, blank=True, default=None,
                                 on_delete=db.SET_NULL)
    component_model = db.ForeignKey('ComponentModel', null=True, blank=True,
                                    verbose_name=_("component model"),
                                    default=None, on_delete=db.SET_NULL)
    user = db.ForeignKey('auth.User', verbose_name=_("user"), null=True,
                         blank=True, default=None, on_delete=db.SET_NULL)
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')


@receiver(pre_save, sender=DeviceModel, dispatch_uid='ralph.history')
def device_model_pre_save(sender, instance, raw, using, **kwargs):
    """
    A hook for creating ``HistoryModelChange`` entries when a device
    model changes.
    """

    for field, orig, new in _field_changes(instance):
        HistoryModelChange(
            device_model=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
        ).save()


@receiver(pre_save, sender=ComponentModel, dispatch_uid='ralph.history')
def component_model_pre_save(sender, instance, raw, using, **kwargs):
    """
    A hook for creating ``HistoryModelChange`` entries when a component
    model changes.
    """

    for field, orig, new in _field_changes(instance):
        HistoryModelChange(
            component_model=instance,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=instance.saving_user,
        ).save()


class DiscoveryValue(db.Model):
    date = db.DateTimeField(default=datetime.now)
    ip = db.IPAddressField(verbose_name=_("IP address"), unique=True)
    plugin = db.CharField(max_length=64, default='')
    key = db.TextField(default='')
    value = db.TextField(default='')
