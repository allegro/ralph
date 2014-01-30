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
                'model_name': 'Cisco Catalyst SOME_CATA_MODEL',
                'type': u'switch',
                'serial_number': 'SOME-SN',
                'mac_adresses': ['AB12BC235556', ],
                'management_ip_addresses': [ip, ],
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
        self.assertEqual(ret, correct_ret)
        network_mock.assertCalledWith(ip)
        command_mock.assert_any_call(
            "show version | include Base ethernet MAC Address",
        )
        command_mock.assert_any_call("show inventory")
        self.assertEqual(command_mock.call_count, 2)
