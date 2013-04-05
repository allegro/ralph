#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.util.zabbix import Zabbix
from ralph.discovery.models import Device, IPAddress
from ralph.util import plugin


class Error(Exception):
    pass


class UpdateError(Error):
    pass


def _calculate_zabbix_templates(role_id):
    from ralph.integration.models import RoleIntegration, IntegrationType
    values = RoleIntegration.objects.filter(
        venture_role__id=role_id,
        type=IntegrationType.zabbix,
        name='template',
    ).values_list('value', flat=True)
    if not values:
        raise UpdateError("No Zabbix integration for this role.")
    return filter(None, values)


def update_zabbix_templates(device, templates=None):
    hostname = device.name   # FIXME: is this deliberate?
    role = device.venture_role
    try:
        ip = device.ipaddress_set.get(hostname=hostname)
    except IPAddress.DoesNotExist:
        return
    if templates is None:
        templates = _calculate_zabbix_templates(role)
    zabbix = Zabbix(settings.ZABBIX_URL, settings.ZABBIX_USER,
                    settings.ZABBIX_PASSWORD)
    zabbix.set_host_templates(hostname, str(ip.address), templates,
                              group_name=settings.ZABBIX_DEFAULT_GROUP)


@plugin.register(chain='zabbix')
def update_role_zabbix_templates(**kwargs):
    role_id = kwargs['uid']
    if not all((
        settings.ZABBIX_URL,
        settings.ZABBIX_USER,
        settings.ZABBIX_PASSWORD,
    )):
        return False, 'Zabbix not configured in settings.', {}
    try:
        templates = _calculate_zabbix_templates(role_id)
        for device in Device.objects.filter(venture_role__id=role_id):
            update_zabbix_templates(device, templates)
        return True, 'done.', kwargs
    except Error:
        return False, 'failed.', kwargs
