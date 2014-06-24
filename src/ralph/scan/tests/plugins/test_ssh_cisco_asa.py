# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django.conf import settings
from mock import patch, MagicMock

settings.SCAN_PLUGINS.update({
    'ralph.scan.plugins.ssh_cisco_asa': {
        'ssh_user': "foo_user",
        'ssh_pass': "foo_pass",
    },
})

from ralph.scan import plugins
from ralph.scan.plugins import ssh_cisco_asa


def cisco_asa_ssh_mock(command):
    if command == "show version | grep (^Hardware|Boot microcode|^Serial|address is)":
        return [
            u'Hardware:   SOME_ASA_MODEL, 12288 MB RAM, CPU AMD Opteron 2600 MHz\r',
            u'                             Boot microcode   : SOME-BOOT-FIRMWARE\r',
            u' 0: Ext: Management0/0       : address is ab12.bc23.5556, irq 11\r',
            u' 1: Ext: Management0/1       : address is ab12.bc23.5558, irq 10\r',
            u' 2: Ext: TenGigabitEthernet5/0: address is def1.13de.4567, irq 11\r',
            u' 3: Ext: TenGigabitEthernet5/1: address is def1.13de.4566, irq 5\r',
            u' 4: Ext: TenGigabitEthernet7/0: address is def1.13de.5677, irq 11\r',
            u' 5: Ext: TenGigabitEthernet7/1: address is def1.13de.5676, irq 5\r',
            u' 6: Ext: TenGigabitEthernet8/0: address is def1.13de.6785, irq 5\r',
            u' 7: Ext: TenGigabitEthernet8/1: address is def1.13de.6784, irq 11\r',
            u'Serial Number: SOME-SN\r'
        ]
    elif command == "show inventory":
        return [
            u'Name: "Chassis", DESCR: "ASA 5580-40 Adaptive Security Appliance"\r',
            u'PID: ASA5580-40        , VID: V01     , SN: SOME-SN\r',
            u'\r',
            u'Name: "module 5", DESCR: "ASA 5580 2 port 10GE SR Fiber Interface Card"\r',
            u'PID: ASA5580-2X10GE-SR , VID: E1572805, SN: def113de4567\r',
            u'\r',
            u'Name: "module 7", DESCR: "ASA 5580 2 port 10GE SR Fiber Interface Card"\r',
            u'PID: ASA5580-2X10GE-SR , VID: E1572805, SN: def113de5677\r',
            u'\r',
            u'Name: "module 8", DESCR: "ASA 5580 2 port 10GE SR Fiber Interface Card"\r',
            u'PID: ASA5580-2X10GE-SR , VID: E1572805, SN: def113de6785\r',
            u'\r'
        ]


class TestCiscoASA(TestCase):

    @patch.object(plugins, 'get_base_result_template')
    @patch.object(ssh_cisco_asa, '_connect_ssh')
    def test_scan(self, connect_mock, tpl_mock):
        self.maxDiff = None
        now = '2013-09-20 11:48:33'
        tpl_mock.return_value = {
            'status': 'unknown',
            'date': now,
            'plugin': 'ssh_cisco_asa',
            'messages': [],
        }
        ip = '10.10.10.10'
        asa_ssh_mock = MagicMock()
        command_mock = MagicMock()
        asa_ssh_mock.asa_command = command_mock
        command_mock.side_effect = cisco_asa_ssh_mock
        connect_mock.return_value = asa_ssh_mock
        correct_ret = {
            'status': 'success',
            'plugin': 'ssh_cisco_asa',
            'messages': [],
            'device': {
                'model_name': 'Cisco SOME_ASA_MODEL',
                'type': 'firewall',
                'serial_number': 'SOME-SN',
                'mac_addresses': [
                    u'AB12BC235556',
                    u'AB12BC235558',
                    u'DEF113DE4567',
                    u'DEF113DE4566',
                    u'DEF113DE5677',
                    u'DEF113DE5676',
                    u'DEF113DE6785',
                    u'DEF113DE6784',
                ],
                'boot_firmware': 'SOME-BOOT-FIRMWARE',
                'management_ip_addresses': [ip, ],
                'memory': [{
                    'size': 12288,
                }],
                'processors': [{
                    'family': 'AMD Opteron',
                    'model_name': 'AMD Opteron',
                    'speed': 2600,
                }],
            },
        }
        ret = ssh_cisco_asa.scan_address(ip, snmp_name='Cisco Software:UCOS')
        correct_ret['date'] = ret['date']  # assuming datetime is working.
        self.assertEqual(ret, correct_ret)
        command_mock.assert_any_call(
            "show version | grep (^Hardware|Boot microcode|^Serial|address is)",
        )
        self.assertEqual(command_mock.call_count, 1)
