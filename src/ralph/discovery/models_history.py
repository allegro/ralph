#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""History models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from ralph.discovery.models_device import (
        Device, DeprecationKind, DeviceModel, DeviceModelGroup
    )
from ralph.discovery.models_device import LoadBalancerMember
from ralph.discovery.models_device import LoadBalancerVirtualServer
from ralph.discovery.models_component import (
        Memory, Processor, Storage, DiskShareMount, DiskShare, Software,
        GenericComponent, Ethernet, FibreChannel, ComponentModel,
        ComponentModelGroup
    )
from ralph.discovery.models_network import IPAddress


FOREVER = '2199-1-1' # not all DB backends will accept '9999-1-1'
ALWAYS = '0001-1-1' # not all DB backends will accept '0000-0-0'


def _field_changes(instance, ignore=('last_seen',)):
    """
    Iterate over all changed fields, yielding the field name,
    its original value and its new value. Skip the fields passed
    in ``ignore``.
    """
    for field, orig in instance.dirty_fields.iteritems():
        if field in ignore:
            continue
        if field in instance.insignificant_fields:
            continue
        if field.endswith('_id'):
            field = field[:-3]
            orig = instance._meta.get_field_by_name(
                    field
                )[0].related.parent_model.objects.get(
                    pk=orig
                ) if orig is not None else None
        try:
            new = getattr(instance, field)
        except AttributeError:
            continue
        yield field, orig, new


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
            return "'{}'.{} = '{}' -> '{}' by {} on {} ({})".format(self.device,
                    self.field_name, self.old_value, self.new_value, self.user,
                    self.date, self.id)


@receiver(pre_save, sender=Device, dispatch_uid='ralph.history')
def device_pre_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries when a device changes."""

    for field, orig, new in _field_changes(instance, ignore={
            'last_seen', 'cached_cost', 'cached_price', 'raw',
            'uptime_seconds', 'uptime_timestamp'}):
        HistoryChange(
                device=instance,
                field_name=field,
                old_value=unicode(orig),
                new_value=unicode(new),
                user=instance.saving_user,
                comment=instance.save_comment,
            ).save()


@receiver(pre_delete, sender=Device, dispatch_uid='ralph.history')
def device_pre_delete(sender, instance, using, **kwargs):
    """A hook for creating ``HistoryChange`` entries when a device is removed."""

    instance.being_deleted = True
    HistoryChange(
        device=None,
        component=unicode(instance),
        field_name='',
        old_value=unicode(instance),
        new_value='',
        user=instance.saving_user,
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
        ).save()


@receiver(pre_save, sender=Memory, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Processor, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Storage, dispatch_uid='ralph.history')
@receiver(pre_save, sender=DiskShareMount, dispatch_uid='ralph.history')
@receiver(pre_save, sender=DiskShare, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Software, dispatch_uid='ralph.history')
@receiver(pre_save, sender=GenericComponent, dispatch_uid='ralph.history')
@receiver(pre_save, sender=Ethernet, dispatch_uid='ralph.history')
@receiver(pre_save, sender=FibreChannel, dispatch_uid='ralph.history')
@receiver(pre_save, sender=IPAddress, dispatch_uid='ralph.history')
@receiver(pre_save, sender=LoadBalancerMember, dispatch_uid='ralph.history')
@receiver(pre_save, sender=LoadBalancerVirtualServer, dispatch_uid='ralph.history')
def device_related_pre_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``HistoryChange`` entry when a component is changed."""

    device = instance.device
    for field, orig, new in _field_changes(instance, ignore={
        'last_seen', 'network_id', 'number', 'hostname', 'last_puppet',
        'dns_info'}):
        HistoryChange(
                device=device,
                field_name=field,
                old_value=unicode(orig),
                new_value=unicode(new),
                user=device.saving_user if device else None,
                component=unicode(instance),
                component_id=instance.id,
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
@receiver(pre_delete, sender=IPAddress, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=LoadBalancerMember, dispatch_uid='ralph.history')
@receiver(pre_delete, sender=LoadBalancerVirtualServer, dispatch_uid='ralph.history')
def device_related_pre_delete(sender, instance, using, **kwargs):
    """A hook for creating ``HistoryChange`` entry when a component is deleted."""

    HistoryChange(
            device=None,
            field_name='',
            old_value=unicode(instance.device),
            new_value='None',
            component=unicode(instance),
            component_id=instance.id,
        ).save()

@receiver(pre_save, sender=DeprecationKind, dispatch_uid='ralph.history')
def deprecationkind_pre_save(sender, instance, raw, using, **kwargs):
    if instance.default:
        items = DeprecationKind.objects.filter(default=True)
        for item in items:
            item.default = False
            item.save()


class HistoryCost(db.Model):
    """
    A single time span for historical cost and venture ownership of a device
    or an extra cost. ``start`` and ``end`` determine the time span during which
    the ``device`` (or ``extra`` cost) was onwed by venture ``venture`` and had
    cost of ``cost``. The time spans for a single device or extra cost should
    never overlap.
    """

    start = db.DateField(default=ALWAYS, null=True)
    end = db.DateField(default=FOREVER)
    daily_cost = db.FloatField(default=0)
    device = db.ForeignKey('Device', null=True, blank=True,
                           default=None, on_delete=db.SET_NULL)
    extra = db.ForeignKey('business.VentureExtraCost', null=True, blank=True,
                           default=None, on_delete=db.SET_NULL)
    venture = db.ForeignKey('business.Venture', null=True, blank=True,
                            default=None, on_delete=db.SET_NULL)

    @classmethod
    def start_span(cls, device=None, extra=None, start='', end=None):
        """
        Start a new time span with new valies for the given device or extra cost.
        It will automatically truncate the previous span if necessary.
        By default, the timespan is infinite towards the future -- possibly to be
        truncated by a later span, but an optional ``end`` parameter can be used
        to specify the end of the timespan.
        """

        item = device or extra
        if not item:
            raise ValueError('Either device or extra is required')
        if start == '':
            start = date.today()
        if device:
            daily_cost = (device.cached_cost or 0)/ 30.4
        else:
            daily_cost = extra.cost / 30.4
        venture = item.venture
        cls.end_span(device=device, extra=extra, end=start)
        span = cls(
                start=start,
                end=end or FOREVER,
                daily_cost=daily_cost,
                device=device,
                extra=extra,
                venture=venture
            )
        span.save()

    @classmethod
    def end_span(cls, device=None, extra=None, end=None):
        """
        Truncates any existings timespans for the specified ``device`` or
        ``extra`` costs, so that a new span can be started at ``end``.
        Implicitly called by ``start_span``.
        """

        if end is None:
            end = date.today()
        for span in cls.objects.filter(device=device, extra=extra, end__gt=end):
            if span.start == end:
                span.delete()
            else:
                span.end = end
                span.save()

    @classmethod
    def filter_span(cls, start, end, query=None):
        """
        Filter a queryset so that only timespans that intersect the span between
        ``start`` and ``end`` with a non-zero overlap are returned.
        """

        if query is None:
            query = cls.objects

        query = query.extra(
            where=[
                "DATEDIFF(LEAST(end, DATE(%s)),GREATEST(start, DATE(%s))) > 0",
            ],
            params=[
                end, start,
            ],
        )
        return query


@receiver(post_save, sender=Device, dispatch_uid='ralph.costhistory')
def cost_post_save(sender, instance, raw, using, **kwargs):
    """
    A hook that updates the HistoryCost spans whenever a cost or venture
    changes on a device, or a device is soft-deleted/undeleted.
    """

    if instance.deleted:
        HistoryCost.end_span(device=instance)
        return
    changed = False
    if 'deleted' in instance.dirty_fields:
        changed = True
    if 'venture_id' in instance.dirty_fields:
        changed = True
    if 'cached_cost' in instance.dirty_fields:
        old_cost = instance.dirty_fields['cached_cost'] or 0
        if not -1 < instance.cached_cost - old_cost < 1:
            # Ignore changes due to rounding errors
            changed = True
    if changed:
        HistoryCost.start_span(device=instance)


@receiver(pre_delete, sender=Device, dispatch_uid='ralph.costhistory')
def cost_pre_delete(sender, instance, using, **kwargs):
    """
    A hook that updates the HistoryCost when a device is deleted.
    """

    HistoryCost.end_span(device=instance)


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
    device_model_group = db.ForeignKey('DeviceModelGroup',
                                 verbose_name=_("device model group"),
                                 null=True, blank=True, default=None,
                                 on_delete=db.SET_NULL)
    component_model_group = db.ForeignKey('ComponentModelGroup', null=True,
                                    blank=True,
                                    verbose_name=_("component model group"),
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
                device_model_group=instance.group,
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
                component_model_group=instance.group,
                field_name=field,
                old_value=unicode(orig),
                new_value=unicode(new),
                user=instance.saving_user,
            ).save()

@receiver(pre_save, sender=DeviceModelGroup, dispatch_uid='ralph.history')
def device_model_pre_save(sender, instance, raw, using, **kwargs):
    """
    A hook for creating ``HistoryModelChange`` entries when a device
    model group changes.
    """

    for field, orig, new in _field_changes(instance):
        HistoryModelChange(
                device_model_group=instance,
                field_name=field,
                old_value=unicode(orig),
                new_value=unicode(new),
                user=instance.saving_user,
            ).save()

@receiver(pre_save, sender=ComponentModelGroup, dispatch_uid='ralph.history')
def component_model_pre_save(sender, instance, raw, using, **kwargs):
    """
    A hook for creating ``HistoryModelChange`` entries when a component
    model group changes.
    """

    for field, orig, new in _field_changes(instance):
        HistoryModelChange(
                component_model_group=instance,
                field_name=field,
                old_value=unicode(orig),
                new_value=unicode(new),
                user=instance.saving_user,
            ).save()

