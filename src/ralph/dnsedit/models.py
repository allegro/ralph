# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db import models as db
from django.utils.translation import ugettext_lazy as _
import ipaddr
from lck.django.common.models import TimeTrackable, MACAddressField
from powerdns.models import Record
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from ralph.discovery.history import field_changes


class DHCPEntry(TimeTrackable):
    mac = MACAddressField(verbose_name=_("MAC address"), unique=True)
    ip = db.CharField(verbose_name=_("IP address"), blank=True, unique=False,
                      default="", max_length=len('xxx.xxx.xxx.xxx'))
    number = db.BigIntegerField(
        _("IP address"), help_text=_("Presented as int."), editable=False,
        unique=False, default=0
    )

    class Meta:
        verbose_name = _("DHCP entry")
        verbose_name_plural = _("DHCP entries")

    def save(self, *args, **kwargs):
        self.number = int(ipaddr.IPAddress(self.ip))
        super(DHCPEntry, self).save(*args, **kwargs)


class DHCPServer(TimeTrackable):
    ip = db.IPAddressField(verbose_name=_("IP address"), unique=True)
    last_synchronized = db.DateTimeField(null=True)
    dhcp_config = db.TextField(blank=True, default='')

    class Meta:
        verbose_name = _('DHCP Server')
        verbose_name_plural = _('DHCP Servers')


class DNSServer(db.Model):
    ip_address = db.IPAddressField(
        verbose_name=_('IP address'),
        unique=True,
    )
    is_default = db.BooleanField(
        verbose_name=_('is default'),
        db_index=True,
        default=False,
    )

    class Meta:
        verbose_name = _('DNS Server')
        verbose_name_plural = _('DNS Servers')

    def __unicode__(self):
        return "DNS Server (%s)" % self.ip_address


class DNSHistory(db.Model):
    date = db.DateTimeField(verbose_name=_("date"),
                            default=datetime.datetime.now)
    user = db.ForeignKey('auth.User', verbose_name=_("user"), null=True,
                         blank=True, default=None, on_delete=db.SET_NULL)
    device = db.ForeignKey('discovery.Device', verbose_name=_("device"),
                           null=True, blank=True, default=None,
                           on_delete=db.SET_NULL)
    record_name = db.CharField(max_length=255, default='')
    record_type = db.CharField(max_length=8, default='')
    field_name = db.CharField(max_length=64, default='')
    old_value = db.CharField(max_length=255, default='')
    new_value = db.CharField(max_length=255, default='')

    class Meta:
        verbose_name = _("DNS History entry")
        verbose_name_plural = _("DNS History entries")


@receiver(post_save, sender=Record, dispatch_uid='ralph.history.dns')
def record_post_save(sender, instance, raw, using, **kwargs):
    for field, orig, new in field_changes(instance, ignore={
            'last_seen', 'change_date', 'id'}):
        DNSHistory(
            record_name=instance.name,
            record_type=instance.type,
            field_name=field,
            old_value=unicode(orig),
            new_value=unicode(new),
            user=getattr(instance, 'saving_user', None),
            device=getattr(instance, 'saving_device', None),
        ).save()


@receiver(pre_delete, sender=Record, dispatch_uid='ralph.history.dns')
def record_pre_delete(sender, instance, using, **kwargs):
    DNSHistory(
        record_name=instance.name,
        record_type=instance.type,
        field_name='deleted',
        old_value=instance.content,
        new_value='',
        user=getattr(instance, 'saving_user', None),
        device=getattr(instance, 'saving_device', None),
    ).save()
