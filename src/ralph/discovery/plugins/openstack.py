#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import plugin
from ralph.discovery.models import (Device, DeviceType, GenericComponent,
    ComponentModel, ComponentType)
from ralph.discovery.models_history import HistoryCost
from ralph.discovery.openstack import OpenStack


@nested_commit_on_success
def make_tenant(tenant):
    dev = Device.create(
            name='OpenStack',
            model_name = 'OpenStack Tenant',
            model_type = DeviceType.cloud_server,
            sn='openstack-%s' % tenant['tenant_id']
        )
    dev.save()
    total_daily_cost = [0]
    def make_component(name, symbol, key, multiplier, unit):
        if key not in tenant:
            return
        model, created = ComponentModel.concurrent_get_or_create(
                type=ComponentType.unknown.id,
                speed=0, cores=0, size=0, family=symbol, extra_hash=''
            )
        if created:
            model.name = name
            model.save()
        res, created = GenericComponent.concurrent_get_or_create(
                model=model, device=dev,
                sn='%s-%s' % (symbol, tenant['tenant_id']))
        if created:
            res.label = unit
        res.save()
        if model.group and model.group.price:
            value = tenant[key] / multiplier
            cost = value * model.group.price / 10000
            total_daily_cost[0] += cost
    make_component('OpenStack 10000 Memory GiB Hours', 'openstackmem',
                   'total_memory_mb_usage', 1024, 'Memory')
    make_component('OpenStack 10000 CPU Hours', 'openstackcpu',
                   'total_vcpus_usage', 1, 'CPU')
    make_component('OpenStack 10000 Disk GiB Hours', 'openstackdisk',
                   'total_local_gb_usage', 1, 'Disk')
    make_component('OpenStack 10000 Volume GiB Hours', 'openstackvolume',
                   'total_volume_gb_usage', 1, 'Volume')
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    today = datetime.date.today()
    dev.historycost_set.filter(start=yesterday).delete()
    hc = HistoryCost(
        device=dev,
        venture=dev.venture,
        start=yesterday,
        end=today,
        daily_cost=total_daily_cost[0],
    )
    hc.save()


@plugin.register(chain='openstack')
def openstack(**kwargs):
    if settings.OPENSTACK_URL is None:
        return False, 'not configured.', kwargs
    stack = OpenStack(
                settings.OPENSTACK_URL,
                settings.OPENSTACK_USER,
                settings.OPENSTACK_PASS,
            )
    end = kwargs.get('end') or datetime.datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0)
    start = kwargs.get('start') or end - datetime.timedelta(days=1)
    for tenant in stack.simple_tenant_usage(start, end):
        make_tenant(tenant)
    return True, 'loaded from %s to %s.' % (start, end), kwargs
