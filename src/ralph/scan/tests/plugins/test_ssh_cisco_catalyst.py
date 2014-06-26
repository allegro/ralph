# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django.conf import settings
from mock import patch, MagicMock

settings.SCAN_PLUGINS.update({
    'ralph.scan.plugins.ssh_cisco_catalyst': {
        'ssh_user': "foo_user",
        'ssh_pass': "foo_pass",
    },
})

from ralph.util import network
from ralph.scan import plugins
from ralph.scan.plugins import ssh_cisco_catalyst


show_version_ret = [
    u'Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 12.2(58)SE2, RELEASE SOFTWARE (fc1)\r',
    u'Technical Support: http://www.cisco.com/techsupport\r',
    u'Copyright (c) 1986-2011 by Cisco Systems, Inc.\r',
    u'Compiled Thu 21-Jul-11 01:23 by prod_rel_team\r',
    u'\r',
    u'ROM: Bootstrap program is C3750E boot loader\r',
    u'BOOTLDR: C3750E Boot Loader (C3750X-HBOOT-M) Version 12.2(53r)SE2, RELEASE SOFTWARE (fc1)\r',
    u'\r',
    u'rack103-sw3 uptime is 1 year, 25 weeks, 2 days, 1 hour, 25 minutes\r',
    u'System returned to ROM by power-on\r',
    u'System restarted at 11:45:06 cet Sun Aug 26 2012\r',
    u'System image file is "flash:/c3750e-universalk9-mz.122-58.SE2/c3750e-universalk9-mz.122-58.SE2.bin"\r',
    u'\r',
    u'\r',
    u'This product contains cryptographic features and is subject to United\r',
    u'States and local country laws governing import, export, transfer and\r',
    u'use. Delivery of Cisco cryptographic products does not imply\r',
    u'third-party authority to import, export, distribute or use encryption.\r',
    u'Importers, exporters, distributors and users are responsible for\r',
    u'compliance with U.S. and local country laws. By using this product you\r',
    u'agree to comply with applicable laws and regulations. If you are unable\r',
    u'to comply with U.S. and local laws, return this product immediately.\r',
    u'\r',
    u'A summary of U.S. laws governing Cisco cryptographic products may be found at:\r',
    u'http://www.cisco.com/wwl/export/crypto/tool/stqrg.html\r',
    u'\r',
    u'If you require further assistance please contact us by sending email to\r',
    u'export@cisco.com.\r',
    u'\r',
    u'License Level: ipservices\r',
    u'License Type: Permanent\r',
    u'Next reload license Level: ipservices\r',
    u'\r',
    u'cisco WS-C3750X-24 (PowerPC405) processor (revision A0) with 262144K bytes of memory.\r',
    u'Processor board ID FFFFFFFFFFD\r',
    u'Last reset from power-on\r',
    u'1 Virtual Ethernet interface\r',
    u'1 FastEthernet interface\r',
    u'56 Gigabit Ethernet interfaces\r',
    u'4 Ten Gigabit Ethernet interfaces\r',
    u'The password-recovery mechanism is enabled.\r',
    u'\r',
    u'512K bytes of flash-simulated non-volatile configuration memory.\r',
    u'Base ethernet MAC Address       : de:ad:be:af:ca:fe\r',
    u'Motherboard assembly number     : 99-99999-99\r',
    u'Motherboard serial number       : FFFFFFFFFFF\r',
    u'Model revision number           : A0\r',
    u'Motherboard revision number     : C0\r',
    u'Model number                    : WS-C3750X-24T-S\r',
    u'Daughterboard assembly number   : 800-32727-01\r',
    u'Daughterboard serial number     : FFFFFFFFFFE\r',
    u'System serial number            : FFFFFFFFFFD\r',
    u'Top Assembly Part Number        : FFF-31327-FF\r',
    u'Top Assembly Revision Number    : E0\r',
    u'Version ID                      : V02\r',
    u'CLEI Code Number                : FFFFFFFFFF\r',
    u'Hardware Board Revision Number  : 0x03\r',
    u'\r',
    u'\r',
    u'Switch Ports Model              SW Version            SW Image                 \r',
    u'------ ----- -----              ----------            ----------               \r',
    u'*    1 30    WS-C3750X-24       12.2(58)SE2           C3750E-UNIVERSALK9-M     \r',
    u'     2 30    WS-C3750X-24       12.2(58)SE2           C3750E-UNIVERSALK9-M     \r',
    u'\r',
    u'\r',
    u'Switch 02\r',
    u'---------\r',
    u'Switch Uptime                   : 1 year, 25 weeks, 2 days, 31 minutes \r',
    u'Base ethernet MAC Address       : de:ad:be:af:ca:ff\r',
    u'Motherboard assembly number     : 99-99999-99\r',
    u'Motherboard serial number       : EEEEEEEEEEE\r',
    u'Model revision number           : A0\r',
    u'Motherboard revision number     : C0\r',
    u'Model number                    : WS-C3750X-24T-S\r',
    u'Daughterboard assembly number   : 800-32727-01\r',
    u'Daughterboard serial number     : FDO15481915\r',
    u'System serial number            : DDDDDDDDDDD\r',
    u'Top assembly part number        : FFF-31327-FF\r',
    u'Top assembly revision number    : E0\r',
    u'Version ID                      : V02\r',
    u'CLEI Code Number                : FFFFFFFFFF\r',
    u'License Level                   : ipservices\r',
    u'License Type                    : Permanent\r',
    u'Next reboot licensing Level     : ipservices\r',
    u'\r',
    u'\r',
    u'Configuration register is 0xF\r',
    u'\r',
    u'rack103-sw3#\r'
]


def ssh_catalyst_mock(command):
    mac_res = [
        u'Base ethernet MAC Address       : AB:12:BC:23:55:56\r',
    ]
    raw_res = [
        u'NAME: "1", DESCR: "SOME_CATA_MODEL"\r',
        u'PID: SOME_CATA_MODEL  , VID: V04  , SN: SOME-SN\r',
        u'\r',
        u'NAME: "GigabitEthernet0/45", DESCR: "1000BaseSX SFP"\r',
        u'PID: Unspecified       , VID:      , SN: eth-sn1        \r',
        u'\r',
        u'NAME: "GigabitEthernet0/46", DESCR: "1000BaseSX SFP"\r',
        u'PID: Unspecified       , VID:      , SN: eth-sn2        \r',
        u'\r',
        u'\r',
    ]
    if command == 'show version | include Base ethernet MAC Address':
        return mac_res
    elif command == 'show inventory':
        return raw_res
    elif command == 'show version':
        return show_version_ret
    elif command == 'terminal length 500':
        return ''
    else:
        raise AssertionError("Wrong command")


class TestCiscoCatalyst(TestCase):

    def setUp(self):
        self.maxDiff = None
        tpl_mock = patch.object(plugins, 'get_base_result_template')
        tpl_mock.return_value = {
            'status': 'unknown',
            'date': '2013-09-20 11:48:33',
            'plugin': 'ssh_cisco_catalyst',
            'messages': [],
        }

    @patch.object(network, 'hostname')
    @patch.object(ssh_cisco_catalyst, '_connect_ssh')
    def test_scan(self, connect_mock, network_mock):
        cata_ssh_mock = MagicMock()
        command_mock = MagicMock()
        cata_ssh_mock.cisco_command = command_mock
        command_mock.side_effect = ssh_catalyst_mock
        connect_mock.return_value = cata_ssh_mock
        ip = '11.11.11.11'
        network_mock.return_value = 'cata1'
        correct_ret = {
            'status': 'success',
            'plugin': 'ssh_cisco_catalyst',
            'messages': [],
            'device': {
                'hostname': 'cata1',
                'model_name': 'Virtual Cisco Catalyst SOME_CATA_MODEL',
                'type': u'Switch stack',
                'serial_number': 'SOME-SN-virtual',
                'mac_adresses': ['AB12BC235556', ],
                'management_ip_addresses': [ip, ],
                'subdevices': [
                    {
                        'serial_number': 'FFFFFFFFFFD',
                        'mac_addresses': ['deadbeafcafe'],
                        'model_name': 'Cisco Catalyst WS-C3750X-24',
                        'installed_software': [
                            {
                                'version': '12.2(58)SE2',
                            }
                        ]
                    },
                    {
                        'serial_number': 'DDDDDDDDDDD',
                        'mac_addresses': ['deadbeafcaff'],
                        'model_name': 'Cisco Catalyst WS-C3750X-24',
                        'installed_software': [
                            {
                                'version': '12.2(58)SE2',
                            }
                        ]
                    }
                ],
                'parts': [
                    {
                        'serial_number': 'eth-sn1',
                        'name': 'GigabitEthernet0/45',
                        'label': '1000BaseSX SFP',
                    },
                    {
                        'serial_number': 'eth-sn2',
                        'name': 'GigabitEthernet0/46',
                        'label': '1000BaseSX SFP',
                    },
                ],
            },
        }
        ret = ssh_cisco_catalyst.scan_address(
            ip,
            http_family='Cisco',
        )
        correct_ret['date'] = ret['date']  # assuming datetime is working.
        self.assertItemsEqual(ret, correct_ret)
        network_mock.assertCalledWith(ip)
        command_mock.assert_any_call(
            "show version | include Base ethernet MAC Address",
        )
        command_mock.assert_any_call("show inventory")
        self.assertEqual(command_mock.call_count, 4)

    def test_get_subswitches(self):
        correct_ret = [
            {
                'serial_number': 'FFFFFFFFFFD',
                'mac_addresses': ['DEADBEAFCAFE'],
                'hostname': 'hostname-1.dc2',
                'model_name': 'Cisco Catalyst WS-C3750X-24',
                'installed_software': [
                    {
                        'version': '12.2(58)SE2',
                    }
                ],
                'type': 'switch',
            },
            {
                'serial_number': 'DDDDDDDDDDD',
                'mac_addresses': ['DEADBEAFCAFF'],
                'model_name': 'Cisco Catalyst WS-C3750X-24',
                'hostname': 'hostname-2.dc2',
                'installed_software': [
                    {
                        'version': '12.2(58)SE2',
                    }
                ],
                'type': 'switch',
            }
        ]
        self.assertEquals(
            ssh_cisco_catalyst.get_subswitches(
                show_version_ret, 'hostname.dc2', '10.20.30.40'),
            correct_ret,
        )
        correct_ret = [
            {
                'serial_number': 'FFFFFFFFFFD',
                'mac_addresses': ['DEADBEAFCAFE'],
                'hostname': '10.20.30.40-1',
                'model_name': 'Cisco Catalyst WS-C3750X-24',
                'installed_software': [
                    {
                        'version': '12.2(58)SE2',
                    }
                ],
                'type': 'switch',
            },
            {
                'serial_number': 'DDDDDDDDDDD',
                'mac_addresses': ['DEADBEAFCAFF'],
                'model_name': 'Cisco Catalyst WS-C3750X-24',
                'hostname': '10.20.30.40-2',
                'installed_software': [
                    {
                        'version': '12.2(58)SE2',
                    }
                ],
                'type': 'switch',
            }
        ]
        self.assertEquals(
            ssh_cisco_catalyst.get_subswitches(
                show_version_ret, None, '10.20.30.40'),
            correct_ret,
        )
