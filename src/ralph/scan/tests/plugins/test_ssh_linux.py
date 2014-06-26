# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.samples.dmidecode_data import DATA
from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.ssh_linux import (
    _get_base_device_info,
    _get_disk_shares,
    _get_hostname,
    _get_mac_addresses,
    _get_os_info,
    _get_os_visible_cores_count,
    _get_os_visible_memory,
    _get_os_visible_storage,
)


GET_MAC_ADDRESSES_RESULT = """\
link/ether c8:2a:14:05:3d:53 brd ff:ff:ff:ff:ff:ff
link/ether e0:f8:47:24:c9:e6 brd ff:ff:ff:ff:ff:ff
"""
GET_OS_VISIBLE_CORES_COUNT_RESULT = """\
processor	: 0
processor	: 1
processor	: 2
processor	: 3
"""
GET_OS_VISIBLE_STORAGE_RESULT = """\
/dev/sda1              22821M 10743M    10933M      50% /
/dev/sda3             274396M 16074M   244586M       7% /home
"""
GET_DISK_SHARES_RESULT_PART_1 = """\
mpath2 (350002ac000123456) dm-11 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:50  sdc 8:32  active undef running
|- 9:0:1:50  sdf 8:80  active undef running
|- 8:0:0:50  sdi 8:128 active undef running
`- 8:0:1:50  sdl 8:176 active undef running
mpath1 (350002ac000123457) dm-7 3PARdata,VV
size=10G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:1:0   sde 8:64  active undef running
|- 9:0:0:0   sdb 8:16  active undef running
|- 8:0:1:0   sdk 8:160 active undef running
`- 8:0:0:0   sdh 8:112 active undef running
mpath3 (350002ac000660910) dm-2 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:100 sdd 8:48  active undef running
|- 9:0:1:100 sdg 8:96  active undef running
|- 8:0:0:100 sdj 8:144 active undef running
`- 8:0:1:100 sdm 8:192 active undef running
"""
GET_DISK_SHARES_RESULT_PART_2 = """\
/dev/mapper/mpath1|VolGroup00|lvm2|a-|10000.11M|0M
/dev/mapper/mpath3|VolGroup01|lvm2|a-|146632.87M|0M
"""
GET_DISK_SHARES_RESULT_PART_3 = """\
LogVol00 VolGroup00 -wi-ao 144552.49M
LogVol01 VolGroup00 -wi-ao   2080.37M
"""


class SshLinuxPluginTest(TestCase):

    def test_get_mac_addresses(self):
        ssh = MockSSH([
            (
                "/sbin/ip addr show | /bin/grep 'link/ether'",
                GET_MAC_ADDRESSES_RESULT,
            )
        ])
        self.assertEqual(
            _get_mac_addresses(ssh),
            ['C82A14053D53', 'E0F84724C9E6'],
        )

    def test_get_hostname(self):
        ssh = MockSSH([('/bin/hostname -f', 'h123123.local')])
        self.assertEqual(_get_hostname(ssh), 'h123123.local')

    def test_get_base_device_info(self):
        ssh = MockSSH([('/usr/bin/sudo /usr/sbin/dmidecode', DATA)])
        self.assertEqual(
            _get_base_device_info(ssh),
            {
                'memory': [
                    {'label': 'PROC 1 DIMM 2A', 'size': 4096, 'speed': 1333},
                    {'label': 'PROC 1 DIMM 4B', 'size': 4096, 'speed': 1333},
                    {'label': 'PROC 2 DIMM 2A', 'size': 4096, 'speed': 1333},
                    {'label': 'PROC 2 DIMM 4B', 'size': 4096, 'speed': 1333},
                ],
                'model_name': 'ProLiant BL460c G6',
                'processors': [
                    {
                        'cores': 4,
                        'family': 'Quad-Core Xeon',
                        'label': 'Proc 1',
                        'model_name': 'Intel(R) Xeon(R) CPU E5506 @ 2.13GHz',
                        'speed': 2133,
                    },
                    {
                        'cores': 4,
                        'family': 'Quad-Core Xeon',
                        'label': 'Proc 2',
                        'model_name': 'Intel(R) Xeon(R) CPU E5506 @ 2.13GHz',
                        'speed': 2133,
                    },
                ],
                'serial_number': 'GB8926V807',
            },
        )

    def test_get_os_visible_cores_count(self):
        ssh = MockSSH([
            (
                "/bin/grep '^processor' '/proc/cpuinfo'",
                GET_OS_VISIBLE_CORES_COUNT_RESULT,
            ),
        ])
        self.assertEqual(_get_os_visible_cores_count(ssh), 4)

    def test_get_os_visible_memory(self):
        ssh = MockSSH([
            (
                "/bin/grep 'MemTotal:' '/proc/meminfo'",
                "MemTotal:        8087080 kB",
            ),
        ])
        self.assertEquals(_get_os_visible_memory(ssh), 7897)

    def test_get_os_visible_storage(self):
        ssh = MockSSH([
            (
                "/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM "
                "| /bin/grep '^/'",
                GET_OS_VISIBLE_STORAGE_RESULT,
            ),
        ])
        self.assertEqual(_get_os_visible_storage(ssh), 297217)

    def test_get_os_info(self):
        ssh = MockSSH([
            (
                '/bin/uname -a',
                'Linux s11968 3.2.0-39-generic #62-Ubuntu SMP '
                'Thu Feb 28 00:28:53 UTC 2013 x86_64 x86_64 x86_64 GNU/Linux',
            ),
            (
                "/bin/grep 'MemTotal:' '/proc/meminfo'",
                "MemTotal:        8087080 kB",
            ),
            (
                "/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM "
                "| /bin/grep '^/'",
                GET_OS_VISIBLE_STORAGE_RESULT,
            ),
            (
                "/bin/grep '^processor' '/proc/cpuinfo'",
                GET_OS_VISIBLE_CORES_COUNT_RESULT,
            ),
        ])
        self.assertEqual(
            _get_os_info(ssh),
            {
                'system_cores_count': 4,
                'system_family': 'Linux',
                'system_label': '#62-Ubuntu 3.2.0-39-generic',
                'system_memory': 7897,
                'system_storage': 297217,
            },
        )

    def test_get_disk_shares(self):
        ssh = MockSSH([
            (
                'multipath -l',
                GET_DISK_SHARES_RESULT_PART_1,
            ),
            (
                "pvs --noheadings --units M --separator '|'",
                GET_DISK_SHARES_RESULT_PART_2,
            ),
            (
                'lvs --noheadings --units M',
                GET_DISK_SHARES_RESULT_PART_3,
            ),
        ])
        self.assertEqual(
            _get_disk_shares(ssh),
            [
                {
                    'serial_number': '50002AC000123457',
                    'size': 10000,
                    'volume': 'VolGroup00'
                },
                {
                    'serial_number': '50002AC000660910',
                    'size': 146632,
                    'volume': 'VolGroup01'
                },
                {
                    'serial_number': '50002AC000123456',
                    'size': 81920,
                    'volume': 'dm-11'
                }
            ]
        )
