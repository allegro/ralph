# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.ssh_juniper import (
    _get_hostname,
    _get_switches,
    _ssh_juniper,
)
from ralph.scan.tests.plugins.samples.ssh_juniper import (
    JUNIPER_NOT_STACKED_SAMPLE,
    JUNIPER_SHOW_VERSION_SAMPLE,
    JUNIPER_STACKED_SAMPLE,
)


class SSHJuniperPluginTest(TestCase):
    def test_get_hostname(self):
        ssh = MockSSH([
            (
                "show version",
                "",
            ),
            (
                "show version",
                JUNIPER_SHOW_VERSION_SAMPLE,
            ),
        ])
        self.assertIsNone(_get_hostname(ssh))
        self.assertEqual(_get_hostname(ssh), 'rack01-sw1.dc')

    def test_get_switches_stacked(self):
        ssh = MockSSH([
            (
                "show virtual-chassis",
                JUNIPER_STACKED_SAMPLE,
            ),
            (
                "show version",
                JUNIPER_SHOW_VERSION_SAMPLE,
            ),
        ])
        self.assertEqual(
            _get_switches(ssh),
            (
                True,
                [
                    {
                        'model': 'ex4500-40f',
                        'role': 'Backup',
                        'serial_number': 'GX1122334401',
                    },
                    {
                        'model': 'ex4500-40f',
                        'role': 'Master*',
                        'serial_number': 'GX1122334402',
                    },
                ],
            ),
        )

    def test_get_switches_not_stacked(self):
        ssh = MockSSH([
            (
                "show virtual-chassis",
                JUNIPER_NOT_STACKED_SAMPLE,
            ),
            (
                "show version",
                JUNIPER_SHOW_VERSION_SAMPLE,
            ),
        ])
        self.assertEqual(
            _get_switches(ssh),
            (
                False,
                [
                    {
                        'model': 'ex4500-40f',
                        'role': 'Master*',
                        'serial_number': 'GX1122334403',
                    },
                ],
            ),
        )

    def test_ssh_juniper_stacked(self):
        ssh = MockSSH([
            (
                "show virtual-chassis",
                JUNIPER_STACKED_SAMPLE,
            ),
            (
                "show version",
                JUNIPER_SHOW_VERSION_SAMPLE,
            ),
        ])
        self.assertEqual(
            _ssh_juniper(ssh, '10.10.10.10'),
            {
                'hostname': 'rack01-sw1.dc',
                'management_ip_addresses': ['10.10.10.10'],
                'model_name': 'Juniper Virtual Chassis Ethernet Switch',
                'subdevices': [
                    {
                        'hostname': 'rack01-sw1-1.dc',
                        'model_name': 'ex4500-40f',
                        'serial_number': 'GX1122334401',
                        'type': 'switch',
                    },
                    {
                        'hostname': 'rack01-sw1-2.dc',
                        'model_name': 'ex4500-40f',
                        'serial_number': 'GX1122334402',
                        'type': 'switch',
                    },
                ],
                'type': 'switch stack',
            },
        )

    def test_ssh_juniper_not_stacked(self):
        ssh = MockSSH([
            (
                "show virtual-chassis",
                JUNIPER_NOT_STACKED_SAMPLE,
            ),
            (
                "show version",
                JUNIPER_SHOW_VERSION_SAMPLE,
            ),
        ])
        self.assertEqual(
            _ssh_juniper(ssh, '10.10.10.10'),
            {
                'hostname': 'rack01-sw1.dc',
                'management_ip_addresses': ['10.10.10.10'],
                'model_name': 'ex4500-40f',
                'serial_number': 'GX1122334403',
                'type': 'switch',
            }
        )
