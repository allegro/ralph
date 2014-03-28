# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.ssh_ssg import _ssh_ssg
from ralph.scan.tests.plugins.samples.ssh_ssg import SSH_SSG_SAMPLE


class SshSsgPluginTest(TestCase):

    def test_ssh_ssg(self):
        with mock.patch(
            'ralph.scan.plugins.ssh_ssg.check_tcp_port',
        ) as check_port, mock.patch(
            'ralph.scan.plugins.ssh_ssg.SSGSSHClient',
        ) as SSH:
            check_port.return_value = True
            SSH.side_effect = MockSSH([
                ('get system', SSH_SSG_SAMPLE),
            ])
            self.assertEqual(
                _ssh_ssg('127.0.0.1', '-', '-'),
                {
                    'hostname': 'SSG-320M',
                    'mac_addresses': ['A0C69A111111'],
                    'management_ip_addresses': ['127.0.0.1'],
                    'model_name': 'SSG-320M REV 14(0)-(00)',
                    'parts': [
                        {
                            'boot_firmware': '6.2.0r10.0',
                            'type': 'power module',
                        },
                    ],
                    'serial_number': 'SN123123999',
                    'type': 'firewall',
                }
            )
