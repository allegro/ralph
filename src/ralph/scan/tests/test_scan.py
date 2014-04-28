# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import IPAddress
from ralph.scan.manual import (
    _get_cleaned_results,
    _get_ip_addresses_from_results,
    _get_results_checksum,
)


class TestScan(TestCase):

    def setUp(self):
        self.ip_2, _ = IPAddress.concurrent_get_or_create(address='127.0.0.2')
        self.ip_3, _ = IPAddress.concurrent_get_or_create(address='127.0.0.3')
        self.ip_5, _ = IPAddress.concurrent_get_or_create(address='127.0.0.5')

    def test_get_ip_addresses_from_results(self):
        ip_addresses = _get_ip_addresses_from_results({
            'plugin_1': {
                'device': {
                    'management_ip_addresses': ['127.0.0.1'],
                    'system_ip_addresses': ['127.0.0.2', '127.0.0.3'],
                },
            },
            'plugin_2': {
                'device': {
                    'management_ip_addresses': ['127.0.0.1', '127.0.0.4'],
                    'foo': 'some value',
                },
            },
            'plugin_3': {
                'device': {
                    'system_ip_addresses': ['127.0.0.5'],
                },
            },
            'plugin_4': {
                'device': {
                    'foo': 'some value',
                },
            },
            'plugin_5': {
                'system_ip_address': ['127.0.0.6'],
            }
        })
        self.assertEqual(
            ip_addresses,
            [
                self.ip_5,
                self.ip_3,
                self.ip_2,
            ],
        )

    def test_clean_results(self):
        raw_data = {
            'plugin_1': {
                'status': 'success',
                'date': '2013-01-01',
                'plugin': 'plugin_1',
                'messages': ['msg 1', 'msg 2'],
                'device': {
                    'key_1': 'val 1 1',
                    'key_2': 'val 2 1',
                }
            },
            'plugin_2': {
                'status': 'error',
                'date': '2013-01-01',
                'device': {
                    'key_1': 'val 1 2',
                    'key_2': 'val 2 2',
                }
            },
        }
        cleaned_data = _get_cleaned_results(raw_data)
        self.assertEqual(
            cleaned_data,
            {
                'plugin_1': {
                    'plugin': 'plugin_1',
                    'device': {
                        'key_1': 'val 1 1',
                        'key_2': 'val 2 1',
                    }
                },
                'plugin_2': {
                    'device': {
                        'key_1': 'val 1 2',
                        'key_2': 'val 2 2',
                    }
                },
            }
        )

    def test_get_results_checksum(self):
        data_1 = {
            'plugin_1': {
                'key_2': 'val 2 1',
                'key_1': 'val 1 1',
            },
            'plugin_2': {
                'key_1': 'val 1 2',
                'key_2': 'val 2 2',
                'key_3': 'val 3 2',
            },
        }
        data_2 = {
            'plugin_2': {
                'key_3': 'val 3 2',
                'key_1': 'val 1 2',
                'key_2': 'val 2 2',
            },
            'plugin_1': {
                'key_1': 'val 1 1',
                'key_2': 'val 2 1',
            },
        }
        self.assertTrue(
            _get_results_checksum(
                data_1,
            ) == _get_results_checksum(
                data_2,
            ) == '124e70669d35effe35d338372e84bce6',
        )
