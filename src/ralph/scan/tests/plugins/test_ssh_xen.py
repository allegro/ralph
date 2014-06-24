# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock

from django.test import TestCase

from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.ssh_xen import (
    _enable_sudo_mode,
    _get_current_host_uuid,
    _get_disks,
    _get_macs,
    _get_running_vms,
    _sanitize_line,
    _ssh_xen,
)
from ralph.scan.tests.plugins.samples.ssh_xen import (
    GET_CURRENT_HOST_UUID_SAMPLE,
    GET_DISKS_SAMPLE,
    GET_MACS_SAMPLE,
    GET_RUNNING_VMS_SAMPLE,
    TEST_SUDO_MODE_SAMPLE,
)


class SSHXenPluginTest(TestCase):

    def test_sanitize_line(self):
        self.assertEqual(
            _sanitize_line('   ala( RO)( RW) ma(MRO) kota '),
            'ala ma kota',
        )

    def test_enable_sudo_mode(self):
        ssh = MockSSH([
            (
                "xe host-list",
                "",
            ),
            (
                "xe host-list",
                TEST_SUDO_MODE_SAMPLE,
            ),
        ])
        self.assertTrue(_enable_sudo_mode(ssh))
        self.assertFalse(_enable_sudo_mode(ssh))

    def test_get_current_host_uuid(self):
        ssh = MockSSH([
            (
                "xe host-list params=address,name-label,uuid",
                GET_CURRENT_HOST_UUID_SAMPLE,
            ),
            (
                "xe host-list params=address,name-label,uuid",
                GET_CURRENT_HOST_UUID_SAMPLE,
            ),
            (
                "xe host-list params=address,name-label,uuid",
                GET_CURRENT_HOST_UUID_SAMPLE,
            ),
        ])
        self.assertEqual(
            _get_current_host_uuid(ssh, '10.10.10.01'),
            'sample-uuid-01',
        )
        self.assertEqual(
            _get_current_host_uuid(ssh, '10.10.10.02'),
            'sample-uuid-02',
        )
        self.assertIsNone(
            _get_current_host_uuid(ssh, '10.10.10.03'),
        )

    def test_get_running_vms(self):
        ssh = MockSSH([
            (
                "xe vm-list resident-on=sample-uuid-01 params="
                "uuid,name-label,power-state,VCPUs-number,memory-actual",
                GET_RUNNING_VMS_SAMPLE,
            ),
        ])
        self.assertEqual(
            _get_running_vms(ssh, 'sample-uuid-01'),
            set(
                [
                    ('app-1', 'vm-sample-uuid-1', 2, 4095),
                    ('app-2', 'vm-sample-uuid-2', 8, 16383),
                    ('app-3', 'vm-sample-uuid-3', 2, 2047),
                    ('app-4', 'vm-sample-uuid-4', 4, 8191),
                    ('app-5', 'vm-sample-uuid-5', 2, 2048),
                    ('app-6', 'vm-sample-uuid-6', 2, 2047),
                ],
            ),
        )

    def test_get_macs(self):
        ssh = MockSSH([
            (
                "xe vif-list params=vm-name-label,MAC",
                GET_MACS_SAMPLE,
            ),
        ])
        self.assertEqual(
            dict(_get_macs(ssh)),
            {
                'app-1': set(['11:22:33:44:55:01', '11:22:33:44:55:02']),
                'app-2': set(['11:22:33:44:55:03']),
                'app-3': set(['11:22:33:44:55:04']),
                'app-4': set(['11:22:33:44:55:05']),
                'app-5': set(['11:22:33:44:55:06']),
                'app-6': set(['11:22:33:44:55:07']),
                'app-7': set(['11:22:33:44:55:08']),
            },
        )

    def test_get_disks(self):
        ssh = MockSSH([
            (
                "xe vm-disk-list vdi-params=sr-uuid,uuid,virtual-size "
                "vbd-params=vm-name-label,type,device --multiple",
                GET_DISKS_SAMPLE,
            ),
        ])
        self.assertEqual(
            dict(_get_disks(ssh)),
            {
                'app-1': [
                    ('uuid-1', 'uuid-2', 24576, 'hda'),
                    ('uuid-5', 'uuid-6', 24576, 'hda'),
                ],
                'app-4': [('uuid-3', 'uuid-4', 51200, 'hda')],
            },
        )

    def test_ssh_xen(self):
        with mock.patch(
            'ralph.scan.plugins.ssh_xen.get_disk_shares',
        ) as get_disk_shares:
            get_disk_shares.return_value = {}
            ssh = MockSSH([
                (
                    "xe host-list",
                    TEST_SUDO_MODE_SAMPLE,
                ),
                (
                    "xe host-list params=address,name-label,uuid",
                    GET_CURRENT_HOST_UUID_SAMPLE,
                ),
                (
                    "xe vm-list resident-on=sample-uuid-01 params="
                    "uuid,name-label,power-state,VCPUs-number,memory-actual",
                    GET_RUNNING_VMS_SAMPLE,
                ),
                (
                    "xe vif-list params=vm-name-label,MAC",
                    GET_MACS_SAMPLE,
                ),
                (
                    "xe vm-disk-list vdi-params=sr-uuid,uuid,"
                    "virtual-size vbd-params=vm-name-label,type,device "
                    "--multiple",
                    GET_DISKS_SAMPLE,
                ),
            ])
            self.assertEqual(
                _ssh_xen(ssh, '10.10.10.01'),
                {
                    'subdevices': [
                        {
                            'disks': [
                                {
                                    'family': 'XEN Virtual Disk',
                                    'label': 'hda',
                                    'size': 24576,
                                },
                                {
                                    'family': 'XEN Virtual Disk',
                                    'label': 'hda',
                                    'size': 24576,
                                },
                            ],
                            'hostname': 'app-1',
                            'mac_addresses': [
                                '112233445501',
                                '112233445502',
                            ],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 4095,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-1',
                        },
                        {
                            'hostname': 'app-3',
                            'mac_addresses': ['112233445504'],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 2047,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-3',
                        },
                        {
                            'hostname': 'app-6',
                            'mac_addresses': ['112233445507'],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 2047,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-6',
                        },
                        {
                            'hostname': 'app-2',
                            'mac_addresses': ['112233445503'],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 16383,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 2,
                                    'label': 'CPU 2',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 3,
                                    'label': 'CPU 3',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 4,
                                    'label': 'CPU 4',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 5,
                                    'label': 'CPU 5',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 6,
                                    'label': 'CPU 6',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 7,
                                    'label': 'CPU 7',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-2',
                        },
                        {
                            'hostname': 'app-5',
                            'mac_addresses': ['112233445506'],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 2048,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-5',
                        },
                        {
                            'disks': [
                                {
                                    'family': 'XEN Virtual Disk',
                                    'label': 'hda',
                                    'size': 51200,
                                },
                            ],
                            'hostname': 'app-4',
                            'mac_addresses': ['112233445505'],
                            'memory': [
                                {
                                    'family': 'Virtual',
                                    'label': 'XEN Virtual',
                                    'size': 8191,
                                },
                            ],
                            'model_name': 'XEN Virtual Server',
                            'processors': [
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 0,
                                    'label': 'CPU 0',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 1,
                                    'label': 'CPU 1',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 2,
                                    'label': 'CPU 2',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                                {
                                    'cores': 1,
                                    'family': 'XEN Virtual',
                                    'index': 3,
                                    'label': 'CPU 3',
                                    'model_name': 'XEN Virtual',
                                    'name': 'XEN Virtual CPU',
                                },
                            ],
                            'serial_number': 'vm-sample-uuid-4',
                        },
                    ],
                    'system_ip_addresses': ['10.10.10.01'],
                    'type': 'unknown',
                },
            )
