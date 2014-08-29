# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.scan.plugins.snmp_lldp import (
    _get_device_interfaces_map,
    _get_remote_connected_ports_map,
    _get_remote_ip_addresses_map,
    _get_remote_mac_addresses_map,
    _snmp_lldp,
)


class SnmpLldpPluginTest(TestCase):

    def test_get_device_interfaces_map(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_lldp.snmp_walk',
        ) as snmp_walk:
            snmp_walk.side_effect = [
                [
                    (("1.0.8802.1.1.2.1.3.7.1.3.1", "Gi0/1"), None),
                    (("1.0.8802.1.1.2.1.3.7.1.3.2", "Gi0/2"), None),
                    (("1.0.8802.1.1.2.1.3.7.1.3.3", "Gi0/3"), None),
                    (("1.0.8802.1.1.2.1.3.7.1.3.4", "Gi0/4"), None),
                ]
            ]
            self.assertEqual(
                _get_device_interfaces_map("10.10.10.10", "public", "2c"),
                {
                    "1": "Gi0/1",
                    "2": "Gi0/2",
                    "3": "Gi0/3",
                    "4": "Gi0/4",
                }
            )

    def test_get_remote_mac_addresses_map(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_lldp.snmp_walk',
        ) as snmp_walk:
            snmp_walk.side_effect = [
                [
                    (
                        (
                            "1.0.8802.1.1.2.1.3.7.1.3.6.1",
                            ['\xff', '\xfe', '\xfd', '\xfc', '\xfb', '\x02']
                        ),
                        None
                    ),
                ]
            ]
            self.assertEqual(
                _get_remote_mac_addresses_map("10.10.10.10", "public", "2c"),
                {"6": "FFFEFDFCFB02"}
            )

    def test_get_remote_ip_addresses_map(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_lldp.snmp_walk',
        ) as snmp_walk:
            snmp_walk.side_effect = [
                [
                    (
                        (
                            "1.0.8802.1.1.2.1.4.2.1.3.0.8.19.1.4.10.10.10.11",
                            0
                        ),
                        None
                    ),
                    (
                        (
                            "1.0.8802.1.1.2.1.4.2.1.3.0.33.19.1.4.10.10.10.12",
                            0
                        ),
                        None
                    ),
                ]
            ]
            self.assertEqual(
                _get_remote_ip_addresses_map("10.10.10.10", "public", "2c"),
                {"8": "10.10.10.11", "33": "10.10.10.12"}
            )

    def test_get_remote_connected_ports_map(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_lldp.snmp_walk',
        ) as snmp_walk:
            snmp_walk.side_effect = [
                [
                    (
                        (
                            "1.0.8802.1.1.2.1.4.1.1.8.0.33.1",
                            "Eth0"
                        ),
                        None
                    ),
                    (
                        (
                            "1.0.8802.1.1.2.1.4.1.1.8.0.42.2",
                            "Eth1"
                        ),
                        None
                    ),
                ]
            ]
            self.assertEqual(
                _get_remote_connected_ports_map("10.10.10.10", "public", "2c"),
                {'33': 'Eth0', '42': 'Eth1'},
            )

    def test_snmp_lldp(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_lldp._get_device_interfaces_map',
        ) as get_device_interfaces_map_mock, mock.patch(
            'ralph.scan.plugins.snmp_lldp._get_remote_mac_addresses_map',
        ) as get_remote_mac_addresses_map_mock, mock.patch(
            'ralph.scan.plugins.snmp_lldp._get_remote_ip_addresses_map',
        ) as get_remote_ip_addresses_map_mock, mock.patch(
            'ralph.scan.plugins.snmp_lldp._get_remote_connected_ports_map',
        ) as get_remote_connected_ports_map_mock:
            get_device_interfaces_map_mock.return_value = {
                "1": "Gi0/1",
                "2": "Gi0/2",
                "3": "Gi0/3",
                "4": "Gi0/4",
                "5": "Gi0/5",
                "6": "Gi0/6",
                "7": "Gi0/7",
                "8": "Gi0/8",
            }
            get_remote_mac_addresses_map_mock.return_value = {
                "2": "FFFEFDFCFB03",
                "3": "FFFEFDFCFB04",
                "9": "FFFEFDFCFBFF",
            }
            get_remote_ip_addresses_map_mock.return_value = {
                "2": "10.0.10.10",
                "3": "10.0.10.11",
                "9": "10.0.10.12",
            }
            get_remote_connected_ports_map_mock.return_value = {
                '2': 'Eth0',
                '3': 'Eth1',
            }
            self.assertEqual(
                _snmp_lldp("10.10.10.11", "public", "2c"),
                {
                    'connections': [
                        {
                            'connected_device_ip_addresses': "10.0.10.12",
                            'connected_device_mac_addresses': 'FFFEFDFCFBFF',
                            'connection_type': 'network',
                        },
                        {
                            'connected_device_ip_addresses': "10.0.10.11",
                            'connected_device_mac_addresses': 'FFFEFDFCFB04',
                            'connection_type': 'network',
                            'details': {
                                'inbound_port': 'Eth1',
                                'outbound_port': 'Gi0/3'
                            }
                        },
                        {
                            'connected_device_ip_addresses': "10.0.10.10",
                            'connected_device_mac_addresses': 'FFFEFDFCFB03',
                            'connection_type': 'network',
                            'details': {
                                'inbound_port': 'Eth0',
                                'outbound_port': 'Gi0/2'
                            }
                        }
                    ],
                    'system_ip_addresses': ['10.10.10.11']
                }
            )
