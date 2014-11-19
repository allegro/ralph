# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.discovery.models import Device, DeviceType, IPAddress
from ralph.scan.plugins.puppet import (
    _get_ip_addresses_hostnames_sets,
    _is_host_virtual,
    _merge_disks_results,
    network,
)


from django.test.utils import override_settings
from ralph.scan.errors import Error, NotConfiguredError
from ralph.scan.plugins.puppet import (
    get_puppet_providers,
    PuppetAPIJsonProvider,
    PuppetDBProvider,
)


existing_file = __file__  # test requires existing file
fake_cert_config = {
    v: existing_file for v in ['ca_cert', 'local_cert', 'local_cert_key']
}


class PuppetPluginTest(TestCase):

    def setUp(self):
        device = Device.create(
            sn='sn_qweasd_123_1',
            model_name='SomeDevice',
            model_type=DeviceType.unknown,
        )
        IPAddress.objects.create(
            address='127.0.0.1',
            hostname='localhost',
            device=device,
        )
        IPAddress.objects.create(
            address='127.0.0.2',
            device=device,
        )

    def test_is_host_virtual(self):
        self.assertFalse(_is_host_virtual({
            'virtual': 'physical',
            'manufacturer': 'Frania',
        }))
        self.assertFalse(_is_host_virtual({
            'manufacturer': 'Frania',
        }))
        self.assertTrue(_is_host_virtual({
            'manufacturer': 'Bochs',
        }))
        self.assertTrue(_is_host_virtual({
            'virtual': 'xen',
        }))

    def test_merge_disks_results(self):
        self.assertEqual(
            _merge_disks_results(
                [
                    {
                        'size': 100000,
                        'label': 'Hitachi',
                        'mount_point': '/mnt/d1',
                        'family': 'Hitachi',
                        'serial_number': 'qwe123_1',
                    },
                    {
                        'size': 100000,
                        'label': 'Hitachi',
                        'mount_point': '/mnt/d2',
                        'family': 'Hitachi',
                        'serial_number': 'qwe123_2',
                    },
                    {
                        'size': 100000,
                        'label': 'Hitachi',
                        'mount_point': '/mnt/n1',
                        'family': 'Hitachi',
                    },
                ],
                [
                    {
                        'size': 100001,
                        'label': 'Hitachi Super',
                        'serial_number': 'qwe123_1',
                    },
                    {
                        'size': 100001,
                        'label': 'Hitachi Super',
                        'serial_number': 'qwe123_3',
                    },
                ]
            ),
            [
                {
                    'family': 'Hitachi',
                    'label': 'Hitachi Super',
                    'mount_point': '/mnt/d1',
                    'serial_number': 'qwe123_1',
                    'size': 100001,
                },
                {
                    'size': 100000,
                    'label': 'Hitachi',
                    'mount_point': '/mnt/d2',
                    'family': 'Hitachi',
                    'serial_number': 'qwe123_2',
                },
                {
                    'family': 'Hitachi',
                    'label': 'Hitachi',
                    'mount_point': '/mnt/n1',
                    'size': 100000,
                },
                {
                    'label': 'Hitachi Super',
                    'serial_number': 'qwe123_3',
                    'size': 100001,
                },
            ],
        )

    @mock.patch.object(network, "hostname")
    def test_get_ip_addresses_hostnames_sets(self, hostname_mock):
        hostname_mock.return_value = None
        self.assertEqual(
            _get_ip_addresses_hostnames_sets('10.123.22.11'),
            ({'10.123.22.11'}, set()),
        )
        hostname_mock.return_value = 'localhost'
        self.assertEqual(
            _get_ip_addresses_hostnames_sets('127.0.0.1'),
            ({'127.0.0.1', '127.0.0.2'}, {'localhost'}),
        )

    def test_getting_puppet_providers_raise_exception(self):
        self.assertRaises(NotConfiguredError, get_puppet_providers)

    @override_settings(PUPPET_API_JSON_URL='https://server:port')
    @mock.patch.object(PuppetDBProvider, '__init__')
    @mock.patch.object(PuppetAPIJsonProvider, '__init__')
    @override_settings(
        PUPPET_DB_URL='mysql://user:password@server:port/db_name'
    )
    def test_api_proivider_is_first(self, db_provider, api_provider):
        db_provider.return_value, api_provider.return_value = None, None
        providers = get_puppet_providers()
        self.assertEqual(len(providers), 2)
        self.assertTrue(isinstance(providers[0], PuppetAPIJsonProvider))

    @mock.patch.object(PuppetDBProvider, '__init__')
    @override_settings(
        PUPPET_DB_URL='mysql://user:password@server:port/db_name'
    )
    def test_db_provider_returned_when_no_api_provider(self, db_provider):
        db_provider.return_value = None
        providers = get_puppet_providers()
        self.assertEqual(len(providers), 1)
        self.assertTrue(isinstance(providers[0], PuppetDBProvider))


class TestPuppetAPIJsonProvider(TestCase):

    @mock.patch.object(PuppetAPIJsonProvider, '_get_data_for_hostname')
    @override_settings(PUPPET_API_JSON_URL='https://server:port')
    @override_settings(PUPPET_API_JSON_CERTS=fake_cert_config)
    def test_get_facts_returns_facts(self, mocked):
        mocked_data = [{'some_key': 'some_value'}, {}]
        mocked.side_effect = mocked_data
        provider = PuppetAPIJsonProvider('api_url')
        hostnames = 'a' * len(mocked_data)
        facts = provider.get_facts([], hostnames, [])
        self.assertEqual(facts, mocked_data[0])

    @mock.patch.object(PuppetAPIJsonProvider, '_get_data_for_hostname')
    @override_settings(PUPPET_API_JSON_URL='https://server:port')
    @override_settings(PUPPET_API_JSON_CERTS=fake_cert_config)
    def test_get_facts_raises_multifounds(self, mocked):
        data = {'some_key': 'some_value'}
        mocked_data = [data, data]
        mocked.side_effect = mocked_data
        provider = PuppetAPIJsonProvider('api_url')
        hostnames = 'a' * len(mocked_data)
        self.assertRaises(
            Error, provider.get_facts, [], hostnames, [],
        )
