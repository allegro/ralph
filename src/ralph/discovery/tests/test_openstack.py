# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import mock

from django.test import TestCase
from django.test.utils import override_settings

from ralph.discovery.models import DeviceType
from ralph.discovery.plugins.openstack import (
    save_tenant,
    openstack
)
from ralph.discovery.tests.util import TenantFactory


TEST_SETTINGS_SITES = dict(
    OPENSTACK_SITES=[
        {
            'TENANT_NAME': 'testtenant',
            'USERNAME': 'testuser',
            'PASSWORD': 'supersecretpass',
            'AUTH_URL': "http://127.0.0.1:5000/v2.0",
            'MODEL_SUFFIX': 'Suffix1',
            'DESCRIPTION': 'OS 1',
        },
        {
            'TENANT_NAME': 'testtenant1',
            'USERNAME': 'testuser',
            'PASSWORD': 'supersecretpass',
            'AUTH_URL': "http://127.0.0.1:5000/v2.0",
            'MODEL_SUFFIX': 'Suffix2',
            'DESCRIPTION': 'OS 2'
        },
    ],
)


class TestOpenstackPlugin(TestCase):
    counter = 0

    @mock.patch('ralph.discovery.plugins.openstack.get_tenants_list')
    @mock.patch('ralph.discovery.plugins.openstack.save_tenant')
    @override_settings(**TEST_SETTINGS_SITES)
    def test_openstack_plugin(self, save_tenant_mock, get_tenants_list_mock):
        save_tenant_mock.return_value = None
        tenants_list = TenantFactory.create_batch(5)
        get_tenants_list_mock.return_value = tenants_list
        result = openstack()
        self.assertEquals(
            result,
            (True, '5 OpenStack Tenants saved', {})
        )
        self.assertEquals(get_tenants_list_mock.call_count, 2)
        self.assertEquals(save_tenant_mock.call_count, 10)
        save_tenant_mock.assert_any_call(
            tenants_list[0].id,
            tenants_list[0].name,
            'OpenStack Tenant Suffix1'
        )
        for site in TEST_SETTINGS_SITES['OPENSTACK_SITES']:
            get_tenants_list_mock.assert_any_call(site)

    def test_openstack_plugin_not_configured(self):
        result = openstack()
        self.assertEquals(result, (False, 'not configured.', {}))

    @mock.patch('ralph.discovery.plugins.openstack.get_tenants_list')
    @mock.patch('ralph.discovery.plugins.openstack.save_tenant')
    @override_settings(OPENSTACK_SITES=[
        {
            'TENANT_NAME': 'testtenant',
            'USERNAME': 'testuser',
            'PASSWORD': 'supersecretpass',
            'AUTH_URL': "http://127.0.0.1:5000/v2.0",
            'DESCRIPTION': 'OS 1',
        }]
    )
    def test_model_suffix_not_configured(
        self,
        save_tenant_mock,
        get_tenants_list_mock
    ):
        save_tenant_mock.return_value = None
        tenants_list = TenantFactory.create_batch(5)
        get_tenants_list_mock.return_value = tenants_list
        result = openstack()
        self.assertEquals(
            result,
            (True, '5 OpenStack Tenants saved', {})
        )
        save_tenant_mock.assert_any_call(
            tenants_list[0].id,
            tenants_list[0].name,
            'OpenStack Tenant'
        )

    def test_save_tenant(self):
        dev = save_tenant('12345', 'tenant1', 'OpenStack Tenant 1')
        self.assertEquals(dev.name, 'tenant1')
        self.assertEquals(dev.sn, 'openstack-12345')
        self.assertEquals(dev.model.name, 'OpenStack Tenant 1')
        self.assertEquals(dev.model.type, DeviceType.cloud_server)
