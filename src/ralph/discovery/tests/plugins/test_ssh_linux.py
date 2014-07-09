#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.util import Eth
from ralph.discovery import hardware
from ralph.discovery.plugins import ssh_linux
from ralph.discovery.tests.util import MockSSH
from ralph.discovery.tests.samples.dmidecode_data import DATA


class SshLinuxPluginTest(TestCase):

    def test_ethernets(self):
        ssh = MockSSH([
            ("/sbin/ip addr show | /bin/grep 'link/ether'", """\
    link/ether c8:2a:14:05:3d:53 brd ff:ff:ff:ff:ff:ff
    link/ether e0:f8:47:24:c9:e6 brd ff:ff:ff:ff:ff:ff
"""),
        ])
        ethernets = ssh_linux.get_ethernets(ssh)
        self.assertEquals(ethernets, [
            Eth('', 'c8:2a:14:05:3d:53', 0),
            Eth('', 'e0:f8:47:24:c9:e6', 0),
        ])

    def test_dmidecode(self):
        ssh = MockSSH([
            ("/usr/bin/sudo /usr/sbin/dmidecode", DATA),
        ])
        dev = ssh_linux.run_dmidecode(ssh, [])
        cpus = [(cpu.label, cpu.model.name, cpu.model.cores, cpu.model.speed)
                for cpu in dev.processor_set.all()]
        self.assertEquals(cpus, [
            (u'Proc 1', u'Intel(R) Xeon(R) CPU E5506 @ 2.13GHz', 4, 2133),
            (u'Proc 2', u'Intel(R) Xeon(R) CPU E5506 @ 2.13GHz', 4, 2133),
        ])
        mem = [(mem.label, mem.model.name, mem.model.size, mem.model.speed)
               for mem in dev.memory_set.all()]
        self.assertEquals(mem, [
            (u'PROC 1 DIMM 2A', u'RAM DDR3 4096MiB, 1333MHz', 4096, 1333),
            (u'PROC 1 DIMM 4B', u'RAM DDR3 4096MiB, 1333MHz', 4096, 1333),
            (u'PROC 2 DIMM 2A', u'RAM DDR3 4096MiB, 1333MHz', 4096, 1333),
            (u'PROC 2 DIMM 4B', u'RAM DDR3 4096MiB, 1333MHz', 4096, 1333),
        ])
        self.assertEquals(dev.model.name, 'DMI ProLiant BL460c G6')

    def test_os_memory(self):
        ssh = MockSSH([
            ("/bin/grep 'MemTotal:' '/proc/meminfo'", """\
MemTotal:        8087080 kB
"""),
        ])
        mem = ssh_linux.get_memory(ssh)
        self.assertEquals(mem, 7897)

    def test_os_cores(self):
        ssh = MockSSH([
            ("/bin/grep '^processor' '/proc/cpuinfo'", """\
processor	: 0
processor	: 1
processor	: 2
processor	: 3
"""),
        ])
        cores = ssh_linux.get_cores(ssh)
        self.assertEquals(cores, 4)

    def test_os_disk(self):
        ssh = MockSSH([
            ("/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM "
             "| /bin/grep '^/'", """\
/dev/sda1              22821M 10743M    10933M      50% /
/dev/sda3             274396M 16074M   244586M       7% /home
"""),
        ])
        disk = ssh_linux.get_disk(ssh)
        self.assertEquals(disk, 297217)

    def test_os_uname(self):
        ssh = MockSSH([
            ("/usr/bin/sudo /usr/sbin/dmidecode", DATA),
            (
                "/bin/uname -a",
                """\
Linux wintermute 3.2.0-29-generic #46-Ubuntu SMP Fri Jul
27 17:03:23 UTC 2012 x86_64 x86_64 x86_64 GNU/Linux
""",
            ),
            (
                "/bin/grep 'MemTotal:' '/proc/meminfo'",
                "MemTotal:        8086784 kB",
            ),
            (
                "/bin/df -P -x tmpfs -x devtmpfs -x ecryptfs -x iso9660 -BM | /bin/grep '^/'",
                """\
/dev/sda1              22529M 18841M     2545M      89% /
/dev/sda3             270416M 37184M   219496M      15% /home
""",
            ),
            (
                "/bin/grep '^processor' '/proc/cpuinfo'",
                """\
processor	: 0
processor	: 1
processor	: 2
processor	: 3
""",
            )
        ])
        dev = ssh_linux.run_dmidecode(ssh, [])
        os = ssh_linux.update_os(ssh, dev)
        self.assertEquals(os.label, '#46-Ubuntu 3.2.0-29-generic')
        self.assertEquals(os.model.name, '#46-Ubuntu')
        self.assertEquals(os.model.family, 'Linux')
        self.assertEquals(os.cores_count, 4)
        self.assertEquals(os.storage, 292945)
        self.assertEquals(os.memory, 7897)

    def test_os_disk_share(self):
        ssh = MockSSH([("multipath -l",
                        """\
mpath2 (350002ac000123456) dm-11 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:50  sdc 8:32  active undef running
|- 9:0:1:50  sdf 8:80  active undef running
|- 8:0:0:50  sdi 8:128 active undef running
`- 8:0:1:50  sdl 8:176 active undef running
mpath3 (350002ac000660910) dm-2 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:100 sdd 8:48  active undef running
|- 9:0:1:100 sdg 8:96  active undef running
|- 8:0:0:100 sdj 8:144 active undef running
`- 8:0:1:100 sdm 8:192 active undef running"""),
                       ("pvs --noheadings --units M --separator '|'", "\
/dev/mapper/mpath3|VolGroup00|lvm2|a-|146632.87M|0M"),
                       ("lvs --noheadings --units M", """\
LogVol00 VolGroup00 -wi-ao 144552.49M
LogVol01 VolGroup00 -wi-ao   2080.37M"""), ])
        storage = hardware.get_disk_shares(ssh)
        self.assertEqual(storage, {
            'dm-11': ('50002AC000123456', 81920),
            'VolGroup00': (u'50002AC000660910', 146632)
        })

    def test_os_disk_share_with_multipath_warning(self):
        ssh = MockSSH([("multipath -l",
                        """\
Jan 01 10:00:00 | multipath.conf line 1, invalid keyword: abcde
Jan 01 10:00:00 | multipath.conf line 2, invalid keyword: qwerty
mpath2 (350002ac000123456) dm-11 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:50  sdc 8:32  active undef running
|- 9:0:1:50  sdf 8:80  active undef running
|- 8:0:0:50  sdi 8:128 active undef running
`- 8:0:1:50  sdl 8:176 active undef running
mpath3 (350002ac000660910) dm-2 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:100 sdd 8:48  active undef running
|- 9:0:1:100 sdg 8:96  active undef running
|- 8:0:0:100 sdj 8:144 active undef running
`- 8:0:1:100 sdm 8:192 active undef running"""),
                       ("pvs --noheadings --units M --separator '|'", "\
/dev/mapper/mpath3|VolGroup00|lvm2|a-|146632.87M|0M"),
                       ("lvs --noheadings --units M", """\
LogVol00 VolGroup00 -wi-ao 144552.49M
LogVol01 VolGroup00 -wi-ao   2080.37M"""), ])
        storage = hardware.get_disk_shares(ssh)
        self.assertEqual(storage, {
            'dm-11': ('50002AC000123456', 81920),
            'VolGroup00': (u'50002AC000660910', 146632)
        })

    def test_os_disk_share_with_wrong_wwn(self):
        # wwn for mpath2 is invalid
        ssh = MockSSH([("multipath -l",
                        """\
mpath2 (350002ac000) dm-11 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:50  sdc 8:32  active undef running
|- 9:0:1:50  sdf 8:80  active undef running
|- 8:0:0:50  sdi 8:128 active undef running
`- 8:0:1:50  sdl 8:176 active undef running
mpath3 (350002ac000660910) dm-2 3PARdata,VV
size=80G features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=-1 status=active
|- 9:0:0:100 sdd 8:48  active undef running
|- 9:0:1:100 sdg 8:96  active undef running
|- 8:0:0:100 sdj 8:144 active undef running
`- 8:0:1:100 sdm 8:192 active undef running"""),
                       ("pvs --noheadings --units M --separator '|'", "\
/dev/mapper/mpath3|VolGroup00|lvm2|a-|146632.87M|0M"),
                       ("lvs --noheadings --units M", """\
LogVol00 VolGroup00 -wi-ao 144552.49M
LogVol01 VolGroup00 -wi-ao   2080.37M"""), ])
        storage = hardware.get_disk_shares(ssh)
        self.assertEqual(storage, {
            'VolGroup00': (u'50002AC000660910', 146632)
        })
