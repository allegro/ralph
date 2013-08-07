# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.scan.plugins.snmp_f5 import _snmp_f5, Error


class SnmpF5PluginTest(TestCase):
    def test_snmp_f5(self):
        with mock.patch(
            'ralph.scan.plugins.snmp_f5.snmp_command',
        ) as snmp_command, mock.patch(
            'ralph.scan.plugins.snmp_f5.snmp_macs',
        ) as snmp_macs:
            # base flow
            snmp_command.side_effect = [
                [[None, 'F5 BIG-IP 8400']],
                [[None, 'bip241990s']],
            ]
            snmp_macs.return_value = [
                '0001D76A7852', '0001D76A7846', '0001D76A784A', '0001D76A784E',
                '0001D76A7851', '0201D76A7851',
            ]
            self.assertEqual(
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
                    '2c',
                ),
                {
                    'mac_addresses': [
                        '0001D76A784E', '0001D76A7846', '0001D76A7852',
                        '0001D76A7851', '0001D76A784A',
                    ],
                    'model_name': 'F5 F5 BIG-IP 8400',
                    'serial_number': 'bip241990s',
                    'type': 'load balancer',
                },
            )
            # not supported snmp name exception
            with self.assertRaises(Error) as context:
                _snmp_f5(
                    '127.0.0.1',
                    'Linux',
                    'public',
                    '2c',
                )
            self.assertTrue(
                'not supported' in context.exception.message.lower(),
            )
            # no valid MAC address exception
            snmp_command.side_effect = [
                [[None, 'F5 BIG-IP 8400']],
                [[None, 'bip241990s']],
            ]
            snmp_macs.return_value = ['0201D76A7852']
            with self.assertRaises(Error) as context:
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
                    '2c',
                )
            self.assertEqual(
                context.exception.message,
                'No valid MAC addresses in the SNMP response.',
            )
            # no answer exception
            snmp_macs.return_value = ['0001D76A7852']
            snmp_command.side_effect = [
                [[None, 'F5 BIG-IP 8400']],
                None,
            ]
            with self.assertRaises(Error) as context:
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
                    '2c',
                )
            self.assertEqual(context.exception.message, 'No answer.')
            # incorrect answer exception
            snmp_command.side_effect = [
                [[None]],
                None,
            ]
            with self.assertRaises(Error) as context:
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
                    '2c',
                )
            self.assertEqual(context.exception.message, 'Incorrect answer.')

