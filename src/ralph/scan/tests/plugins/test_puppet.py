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
