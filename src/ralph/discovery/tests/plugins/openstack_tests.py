# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock
from django.test import TestCase
from django.conf import settings

from ralph.discovery.plugins.openstack import (openstack as openstack_runner,
    make_tenant)
from ralph.discovery.tests.plugins.samples.openstack import simple_tenant_usage_data
from ralph.discovery.models import (Device, ComponentModel, GenericComponent,
        MarginKind, ComponentModelGroup)
from ralph.discovery.models_history import HistoryCost


class MockOpenStack(object):
    """ Simple mock for OpenStack network library """
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def simple_tenant_usage(self, start, end):
        return simple_tenant_usage_data

    def query(self, query, url, **kwargs):
        pass

    def auth(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return mock.Mock()


class OpenStackPluginTest(TestCase):
    """ OpenStack costs Test Case """

    def setUp(self):
        # fake settings needed to run plugin, even with mocked library.
        settings.OPENSTACK_URL = '/'
        settings.OPENSTACK_USER = 'test'
        settings.OPENSTACK_PASSWORD = 'test'
        # model group for sample costs calculations.
        self.cmg = ComponentModelGroup()
        self.cmg.price = 100.0
        self.cmg.per_size = 1
        self.cmg.size_modifier = 1
        self.cmg.save()
        self.mk = MarginKind()
        self.mk.margin = 200
        self.mk.remarks = 'Margin kind 200%'
        self.mk.save()

    def test_plugin(self):
        """
        Black box for openstack plugin
        """
        with mock.patch('ralph.discovery.plugins.openstack.OpenStack') as OpenStack:
            OpenStack.side_effect = MockOpenStack
            openstack_runner()
            # testdata has 47 entries.
            self.assertEqual(47, HistoryCost.objects.count())
            # if no group assigned, daily cost = 0 for all historycost
            self.assertEqual(0, sum([x.daily_cost for x in HistoryCost.objects.all()]))
            # if we assign them to the group ...
            for x in ComponentModel.objects.all():
                x.group=self.cmg
                x.save()
            # and run again openstack runner
            openstack_runner()
            # data couns will be the same (data overwritten)
            self.assertEqual(47, HistoryCost.objects.count())
            # costs will be calculated as below.
            self.assertEqual(31733606.18055556, sum([x.daily_cost for x in HistoryCost.objects.all()]))
            # now test with marginkind
            for x in Device.objects.filter(model__name='OpenStack Tenant'):
                x.margin_kind = self.mk
                x.save()
            openstack_runner()
            # margin kind = 200% = multiplies costs 3 times.
            self.assertEqual(31733606.18055556*3, sum([x.daily_cost for x in HistoryCost.objects.all()]))

    def test_make_tenant(self):
        """
        Detailed test for make_tenant plugin sub-function
        """
        tenant_params = dict(
                tenant_id='3ff63bf0e1384a1d87b6eaba8dad1196',
                total_volume_gb_usage=1,
                total_memory_mb_usage=1024,
                total_local_gb_usage=1,
                total_hours=1,
                total_vcpus_usage=1,
                tenant_fake=999,
        )
        with mock.patch('ralph.discovery.plugins.openstack.OpenStack') as OpenStack:
            OpenStack.side_effect = MockOpenStack
            result = make_tenant(tenant_params)
            # no componentModel assigned to the group. Cost will be 0
            self.assertEqual(result[1], 0)

            d=Device.objects.get(model__name='OpenStack Tenant')
            self.assertEqual(d.model.get_type_display(), 'cloud server')
            self.assertEqual(d.sn, 'openstack-3ff63bf0e1384a1d87b6eaba8dad1196')
            # only recognized component models auto-created.
            self.assertEqual(set([
                u'OpenStack 10000 Memory GiB Hours',
                u'OpenStack 10000 CPU Hours',
                u'OpenStack 10000 Disk GiB Hours',
                u'OpenStack 10000 Volume GiB Hours']),
                set([x.name for x in ComponentModel.objects.all()]))
            # only recognized components auto-created.
            self.assertEqual(set([
                u'OpenStack 10000 Memory GiB Hours',
                u'OpenStack 10000 CPU Hours',
                u'OpenStack 10000 Disk GiB Hours',
                u'OpenStack 10000 Volume GiB Hours']),
                set([x.model.name for x in GenericComponent.objects.all()]))
            # and every component is binded to open stack tenant device
            for x in GenericComponent.objects.all():
                self.assertEqual(x.device.model.name, 'OpenStack Tenant')
            # if we assign 2 component model items into the specified group than...
            for i in ComponentModel.objects.all()[0:2]:
                i.group=self.cmg
                i.save()
            # then the costs of half components appears when reimporting tenant. \
            # Rest of components are unassigned to the group, so not counted
            result = make_tenant(tenant_params)
            self.assertEqual(result[1], 200.0)

