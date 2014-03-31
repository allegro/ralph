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
        ) as snmp_command:
            # base flow
            snmp_command.side_effect = [
                [[None, 'F5 BIG-IP 8400']],
                [[None, 'bip241990s']],
            ]
            self.assertEqual(
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
                ),
                {
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
                )
            self.assertTrue(
                'not supported' in context.exception.message.lower(),
            )
            # no answer exception
            snmp_command.side_effect = [
                [[None, 'F5 BIG-IP 8400']],
                None,
            ]
            with self.assertRaises(Error) as context:
                _snmp_f5(
                    '127.0.0.1',
                    'Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app',
                    'public',
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
                )
            self.assertEqual(context.exception.message, 'Incorrect answer.')
