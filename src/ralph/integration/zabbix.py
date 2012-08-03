#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from celery.task import task

from ralph.util.zabbix import Zabbix
from ralph.integration.models import IntegrationType
from ralph.discovery.models import IPAddress
from ralph.business.models import VentureRole
from ralph.util import plugin


class Error(Exception):
    pass

class UpdateError(Error):
    pass


def _calculate_zabbix_templates(role):
    values = role.roleintegration_set.filter(
        type=IntegrationType.zabbix.id
    ).filter(
        name='template'
    ).values_list('value')
    if not values:
        raise UpdateError("No Zabbix integration for this role.")
    templates = [value for value, in values if value]
    return templates


@task(ignore_result=True, queue='zabbix')
def zabbix_update_task(hostname, ip, templates):
    if not settings.ZABBIX_URL:
        return
    zabbix = Zabbix(settings.ZABBIX_URL, settings.ZABBIX_USER,
                    settings.ZABBIX_PASSWORD)
    zabbix.set_host_templates(hostname, ip, templates,
            group_name=settings.ZABBIX_DEFAULT_GROUP)


def update_zabbix_templates(device, templates=None, remote=False):
    hostname = device.name
    role = device.venture_role
    try:
        ip = device.ipaddress_set.get(hostname=hostname)
    except IPAddress.DoesNotExist:
        return
    if templates is None:
        templates = _calculate_zabbix_templates(role)
    if remote:
        task = zabbix_update_task.delay
    else:
        task = zabbix_update_task
    task(hostname, str(ip.address), templates)


def update_role_zabbix_templates(role, remote=False):
    templates = _calculate_zabbix_templates(role)
    for device in role.device_set.all():
        update_zabbix_templates(device, templates, remote=remote)


@plugin.register(chain='zabbix')
def zabbix(remote, **args):
    for role in VentureRole.objects.filter(
            roleintegration__type=IntegrationType.zabbix.id
        ):
        update_role_zabbix_templates(role, remote)
    return True, 'done.', {}

