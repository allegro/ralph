# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.discovery.models import DeviceType, MAC_PREFIX_BLACKLIST
from ralph.scan.plugins.snmp_macs import (
    _get_model_info,
    _snmp_mac,
    _snmp_modular_macs,
    _snmp_vmware_macs,
    Error,
)


class SnmpMacsPluginTest(TestCase):

    def test_get_model_info(self):
        self.assertRaises(Error, _get_model_info, 'bla bla bla')
        self.assertEqual(
            _get_model_info('ubuntu linux'),
            ('Linux', DeviceType.unknown, False),
        )
        self.assertEqual(
            _get_model_info('Fibre Channel Switch'),
            ('Fibre Channel Switch', DeviceType.fibre_channel_switch, True),
        )

    def test_snmp_mac(self):
        with mock.patch('ralph.scan.plugins.snmp_macs.snmp_macs') as snmp_macs:
            # base flow
            snmp_macs.return_value = ['001A643320EA']
            run_params = {
                'ip_address': '127.0.0.1',
                'snmp_name': 'Linux 2.6.9-42.0.10.plus.c4smp #1 SMP i686',
                'snmp_community': 'public',
                'snmp_version': '2c',
            }
            self.assertEqual(
                _snmp_mac(**run_params),
                {
                    'system_ip_addresses': ['127.0.0.1'],
                    'type': 'unknown',
                    'model_name': 'Linux',
                    'mac_addresses': ['001A643320EA'],
                },
            )
            # no snmp_name or snmp_community
            with self.assertRaises(Error) as context:
                _snmp_mac(
                    '127.0.0.1',
                    '',
                    'public',
                    '2c',
                )
            self.assertTrue(
                'empty snmp name or community'
                in context.exception.message.lower(),
            )
            with self.assertRaises(Error) as context:
                _snmp_mac(
                    '127.0.0.1',
                    'Linux',
                    '',
                    '2c',
                )
            self.assertTrue(
                'empty snmp name or community'
                in context.exception.message.lower(),
            )
            # no mac address
            snmp_macs.return_value = []
            with self.assertRaises(Error) as context:
                _snmp_mac(**run_params)
            self.assertTrue(
                'no valid mac' in context.exception.message.lower(),
            )
            # virtual device mac
            snmp_macs.return_value = [
                "%s332211" % iter(MAC_PREFIX_BLACKLIST).next(),
            ]
            with self.assertRaises(Error) as context:
                _snmp_mac(**run_params)
            self.assertTrue(
                'no valid mac' in context.exception.message.lower(),
            )
            # Brocade switch
            run_params['snmp_name'] = 'Brocade'
            snmp_macs.return_value = ['001A643320EA']
            with self.assertRaises(Error) as context:
                _snmp_mac(**run_params)
            self.assertTrue(
                'no valid mac' in context.exception.message.lower(),
            )
            # VMWare interface on Windows
            run_params['snmp_name'] = 'hardware: Windows'
            snmp_macs.return_value = ['000C293320EA']
            with self.assertRaises(Error) as context:
                _snmp_mac(**run_params)
            self.assertTrue(
                'no valid mac' in context.exception.message.lower(),
            )
            # f5
            run_params['snmp_name'] = 'Linux'
            snmp_macs.return_value = ['0001D7112233', '0201D7112233']
            self.assertEqual(
                _snmp_mac(**run_params),
                {
                    'mac_addresses': ['0001D7112233'],
                    'model_name': 'F5',
                    'system_ip_addresses': ['127.0.0.1'],
                    'type': 'load balancer',
                },
            )
            # test sn detection...
            run_params['snmp_name'] = 'IronPort 1, Serial #: qwe123'
            snmp_macs.return_value = ['001A643320EA']
            self.assertEqual(
                _snmp_mac(**run_params),
                {
                    'management_ip_addresses': ['127.0.0.1'],
                    'sn': 'qwe123',
                    'type': 'SMTP gateway',
                    'model_name': 'IronPort 1',
                    'mac_addresses': ['001A643320EA'],
                },
            )
            run_params['snmp_name'] = 'APC type 1 SN:   asd123'
            self.assertEqual(
                _snmp_mac(**run_params),
                {
                    'management_ip_addresses': ['127.0.0.1'],
                    'sn': 'asd123',
                    'type': 'power distribution unit',
                    'model_name': 'APC',
                    'mac_addresses': ['001A643320EA'],
                },
            )

    def test_snmp_vmware_macs(self):
        with mock.patch('ralph.scan.plugins.snmp_macs.snmp_macs') as snmp_macs:
            snmp_macs.return_value = ['001A643320EA', '001A643320EB']
            self.assertEqual(
                _snmp_vmware_macs(
                    ip_address='127.0.0.1',
                    snmp_community='public',
                ),
                [
                    {
                        'mac_addresses': ['001A643320EA'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'VMware ESX virtual server',
                        'type': 'virtual server',
                    },
                    {
                        'mac_addresses': ['001A643320EB'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'VMware ESX virtual server',
                        'type': 'virtual server',
                    },
                ],
            )

    def test_snmp_modular_macs(self):
        def macs_side(ip, community, oid, *args, **kwargs):
            return {
                1: set([
                    u'001E670C5960', u'001E67123169', u'001E67123168',
                    u'001E670C5961', u'001E670C53BD', u'001E6710DD9D',
                    u'001E6710DD9C', u'001E670C53BC', u'001E671232F5',
                    u'001E671232F4', u'001E670C5395', u'001E670C5394',
                ]),
                2: set([
                    u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                    u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                    u'001E671232F5', u'001E671232F4', u'001E670C5395',
                    u'001E670C5394',
                ]),
                3: set([
                    u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                    u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                    u'001E670C5395', u'001E670C5394',
                ]),
                4: set([
                    u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                    u'001E670C53BC', u'001E670C5395', u'001E670C5394',
                ]),
                5: set([
                    u'001E670C5960', u'001E670C5961', u'001E670C5395',
                    u'001E670C5394',
                ]),
                6: set([u'001E670C5960', u'001E670C5961']),
            }[oid[-1]]
        with mock.patch(
            'ralph.scan.plugins.snmp_macs.snmp_macs',
        ) as snmp_macs, mock.patch(
            'ralph.scan.plugins.snmp_macs.snmp_command',
        ) as snmp_command:
            snmp_macs.side_effect = macs_side
            snmp_command.return_value = [[None, 6]]
            self.assertEqual(
                _snmp_modular_macs(
                    ip_address='127.0.0.1',
                    ip_address_is_management=True,
                    snmp_community='public',
                ),
                [
                    {
                        'chassis_position': 1,
                        'mac_addresses': ['001E67123168', '001E67123169'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 2,
                        'mac_addresses': ['001E671232F5', '001E671232F4'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 3,
                        'mac_addresses': ['001E6710DD9D', '001E6710DD9C'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 4,
                        'mac_addresses': ['001E670C53BD', '001E670C53BC'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 5,
                        'mac_addresses': ['001E670C5395', '001E670C5394'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                    {
                        'chassis_position': 6,
                        'mac_addresses': ['001E670C5960', '001E670C5961'],
                        'management_ip_addresses': ['127.0.0.1'],
                        'model_name': 'Intel Modular Blade',
                        'type': 'blade server',
                    },
                ],
            )
