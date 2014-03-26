#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import collections

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
        model_name='OpenStack Tenant',
        model_type=DeviceType.cloud_server,
        sn='openstack-%s' % tenant
    )
    dev.save()
    return dev


def make_components(tenant, dev, region):
    total_daily_cost = [0]

    def make_component(name, symbol, key, multiplier, unit):
        if key not in tenant:
            return
        model, created = ComponentModel.create(
            ComponentType.unknown,
            family=symbol,
            name=name,
            priority=0,
        )
        res, created = GenericComponent.concurrent_get_or_create(
            sn='%s-%s-%s' % (symbol, tenant['tenant_id'], region),
            defaults=dict(
                model=model,
                device=dev,
            ),
        )

        if created:
            res.label = unit
        res.save()
        if model.group and model.group.price:
            value = tenant[key] / multiplier
            cost = value * model.group.price / (model.group.size_modifier or 1)
            total_daily_cost[0] += cost
    make_component('OpenStack 10000 Memory GiB Hours', 'openstackmem',
                   'total_memory_mb_usage', 1024, 'Memory')
    make_component('OpenStack 10000 CPU Hours', 'openstackcpu',
                   'total_vcpus_usage', 1, 'CPU')
    make_component('OpenStack 10000 Disk GiB Hours', 'openstackdisk',
                   'total_local_gb_usage', 1, 'Disk')
    make_component('OpenStack 10000 Volume GiB Hours', 'openstackvolume',
                   'total_volume_gb_usage', 1, 'Volume')
    make_component('OpenStack 10000 Images GiB Hours', 'openstackimages',
                   'total_images_gb_usage', 1, 'Images')
    return total_daily_cost[0]


@plugin.register(chain='openstack')
def openstack(**kwargs):
    if settings.OPENSTACK_URL is None:
        return False, 'not configured.', kwargs
    tenants = collections.defaultdict(lambda: collections.defaultdict(dict))
    end = kwargs.get('end') or datetime.datetime.today().replace(
        hour=0, minute=0, second=0, microsecond=0)
    start = kwargs.get('start') or end - datetime.timedelta(days=1)
    for region in getattr(settings, 'OPENSTACK_REGIONS', ['']):
        stack = OpenStack(
            settings.OPENSTACK_URL,
            settings.OPENSTACK_USER,
            settings.OPENSTACK_PASS,
            region=region,
        )
        for data in stack.simple_tenant_usage(start, end):
            tenants[data['tenant_id']][region].update(data)
    for url, query in getattr(settings, 'OPENSTACK_EXTRA_QUERIES', []):
        for data in stack.query(query, url=url,
                                start=start.strftime('%Y-%m-%dT%H:%M:%S'),
                                end=end.strftime('%Y-%m-%dT%H:%M:%S'),
                                ):
            tenants[data['tenant_id']][url].update(data)
    for tenant_id, regions in tenants.iteritems():
        dev = make_tenant(tenant_id)
        dev.historycost_set.filter(start=start).delete()
        margin_in_percent = dev.get_margin() or 0
        total_cost = 0
        for region, data in regions.iteritems():
            cost = make_components(data, dev, region)
            total_cost += cost * (1 + margin_in_percent / 100)
        hc = HistoryCost(
            device=dev,
            venture=dev.venture,
            start=start,
            end=end,
            daily_cost=total_cost,
        )
        hc.save()
    return True, 'loaded from %s to %s.' % (start, end), kwargs
