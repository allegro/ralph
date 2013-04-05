# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.contrib.auth.models import User
from tastypie.test import ResourceTestCase

from ralph.business.models import Venture
from ralph.discovery.models import (
    ComponentModel,
    ComponentModelGroup,
    ComponentType,
    DeprecationKind,
    DeviceType,
    SplunkUsage
)
from ralph.ui.tests.util import create_device, create_model


class DeviceWithPricingResourceTest(ResourceTestCase):
    def setUp(self):
        super(DeviceWithPricingResourceTest, self).setUp()
        self.resource = 'devicewithpricing'
        self.user = User.objects.create_user(
            'ralph',
            'ralph@ralph.local',
            'ralph'
        )

        self.venture = Venture(name='Infra').save()
        self.deprecation_kind = DeprecationKind(
            name='12 months',
            months=12
        ).save()
        srv1 = {
            'sn': 'srv-1',
            'model_name': 'server',
            'model_type': DeviceType.virtual_server,
            'venture': self.venture,
            'name': 'Srv 1',
            'purchase_date': datetime.datetime(2020, 1, 1, 0, 0),
            'deprecation_kind': self.deprecation_kind,
        }
        srv1_cpu = {
            'model_name': 'Intel PCU1',
            'label': 'CPU 1',
            'priority': 0,
            'family': 'Intsels',
            'price': 120,
            'count': 2,
            'speed': 1200,
        }
        srv1_memory = {
            'priority': 0,
            'family': 'Noname RAM',
            'label': 'Memory 1GB',
            'price': 100,
            'speed': 1033,
            'size': 512,
            'count': 6,
        }
        srv1_storage = {
            'model_name': 'Store 1TB',
            'label': 'store 1TB',
            'priority': 0,
            'family': 'Noname Store',
            'price': 180,
            'count': 10,
        }
        self.device = create_device(
            device=srv1,
            cpu=srv1_cpu,
            memory=srv1_memory,
            storage=srv1_storage,
        )
        self.device.save()

        name = 'Splunk Volume 100 GiB'
        symbol = 'splunkvolume'
        model, created = ComponentModel.create(
            ComponentType.unknown,
            family=symbol,
            name=name,
            priority=0,
        )
        model_group, created = ComponentModelGroup.objects.get_or_create(
            name='Group Splunk',
            price=128,
            type=ComponentType.unknown,
        )
        model.group = model_group
        model.save()

        res, created = SplunkUsage.concurrent_get_or_create(
            device=self.device,
            day=datetime.date.today(),
            defaults={'model': model},
        )
        res.size = 10
        res.save()

    def test_get_list_json(self):
        resp = self.api_client.get(
            '/api/v0.9/{0}/'.format(self.resource),
            format='json',
        )
        self.assertValidJSONResponse(resp)
        device = self.deserialize(resp)['objects'][0]
        self.assertEqual(device['id'], 1)
        self.assertEqual(device['name'], 'Srv 1')
        self.assertEqual(device['sn'], 'srv-1')
        self.assertEqual(device['total_cost'], 2640)
        self.assertDictEqual(
            device['splunk'],
            {
                'splunk_size': 10,
                'splunk_monthly_cost': 128.0,
                'splunk_daily_cost': 128.0
            }
        )
