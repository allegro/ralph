#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import datetime


from django.core.management.base import BaseCommand
from django.conf import settings
#from lck.django.common import nested_commit_on_success

from ralph.discovery.models import (Device, DeviceType, GenericComponent,
    ComponentModel, ComponentType)
from ralph.discovery.models_history import HistoryCost
from ralph.util.openstack import OpenStack


class Command(BaseCommand):
    """Update the billing data from OpenStack"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        stack = OpenStack(
                    settings.OPENSTACK_URL,
                    settings.OPENSTACK_USER,
                    settings.OPENSTACK_PASS,
                )
        end = datetime.datetime.today().replace(hour=0,minute=0,second=0)
        start = end - datetime.timedelta(days=1)
        print('start=%r, end=%r' % (start, end))
        for tenant in stack.simple_tenant_usage(start, end):
            print('tenant_id=%r' % tenant['tenant_id'])
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
                    print('name=%r' % name)
                    value = tenant[key] / multiplier
                    print('value=%r' % value)
                    cost = value * model.group.price / 10000
                    print('cost=%r' % cost)
                    total_daily_cost[0] += cost
                    print('total cost=%r' % total_daily_cost[0])
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

