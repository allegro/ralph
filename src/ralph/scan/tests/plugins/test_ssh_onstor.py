# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from mock import MagicMock, patch

from ralph.discovery.models import DiskShare, Device
from ralph.scan.plugins import ssh_onstor
from ralph.util import parse


class SshClientMock():
    def __init__(self, stdin='', stdout='', stderr=''):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def exec_command(self, command):
        return (
            MagicMock(read=MagicMock(return_value=self.stdin)),
            MagicMock(
                read=MagicMock(return_value=self.stdout),
                readlines=MagicMock(return_value=self.stdout),
            ),
            MagicMock(read=MagicMock(return_value=self.stderr)),
        )


class SshOnstorPluginTest(TestCase):
    def test__convert_unit_when_M(self):
        self.assertEqual(
            ssh_onstor._convert_unit('10 M'),
            10,
        )

    def test__convert_unit_when_G(self):
        self.assertEqual(
            ssh_onstor._convert_unit('10 G'),
            10240,
        )

    def test__convert_unit_when_T(self):
        self.assertEqual(
            ssh_onstor._convert_unit('10 T'),
            10485760,
        )

    def test__get_wwn_when_diskshare_not_exist(self):
        self.assertEqual(
            ssh_onstor._get_wwn('3PAR_testwwn'),
            'testwwn',
        )

    def test__get_wwn_when_multi_value_matched(self):
        DiskShare.objects.create(
            wwn='1testwwn',
            device_id=Device.objects.create().id,
        )
        DiskShare.objects.create(
            wwn='2testwwn',
            device_id=Device.objects.create().id,
        )
        self.assertEqual(
            ssh_onstor._get_wwn('3PAR_testwwn'),
            'testwwn',
        )

    def test__get_wwn(self):
        DiskShare.objects.create(
            wwn='mytestwwn',
            device_id=Device.objects.create().id,
        )
        self.assertEqual(
            ssh_onstor._get_wwn('3PAR_testwwn'),
            'mytestwwn',
        )

    def test__get_disk_share_when_splited_line_not_exist(self):
        self.assertEqual(
            ssh_onstor._get_disk_share(SshClientMock(stdout=[''])),
            [],
        )

    def test__get_disk_share_when_splited_line_is_not_OPENED(self):
        self.assertEqual(
            ssh_onstor._get_disk_share(SshClientMock(stdout=['CLOSED test'])),
            [],
        )

    @patch.object(parse, 'pairs', MagicMock())
    @patch.object(ssh_onstor, '_convert_unit', lambda x: 10)
    @patch.object(ssh_onstor, '_get_wwn', lambda x: 'testwwn')
    def test__get_disk_share(self):
        self.assertEqual(
            ssh_onstor._get_disk_share(SshClientMock(stdout=['OPENED test'])),
            [{u'serial_number': u'testwwn', u'size': 10, u'volume': None}],
        )