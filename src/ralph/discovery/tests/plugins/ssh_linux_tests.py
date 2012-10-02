#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.util import Eth
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
            (u'PROC 1 DIMM 2A', u'RAM DDR3 4096MiB', 4096, 1333),
            (u'PROC 1 DIMM 4B', u'RAM DDR3 4096MiB', 4096, 1333),
            (u'PROC 2 DIMM 2A', u'RAM DDR3 4096MiB', 4096, 1333),
            (u'PROC 2 DIMM 4B', u'RAM DDR3 4096MiB', 4096, 1333),
        ])
        self.assertEquals(dev.model.name, 'ProLiant BL460c G6')

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
            ("/bin/uname -a", """\
Linux wintermute 3.2.0-29-generic #46-Ubuntu SMP Fri Jul 27 17:03:23 UTC 2012 x86_64 x86_64 x86_64 GNU/Linux
"""),
        ])
        dev = ssh_linux.run_dmidecode(ssh, [])
        os = ssh_linux.make_system(ssh, dev)
        self.assertEquals(dev.name, 'wintermute')
        self.assertEquals(os.label, '#46-Ubuntu 3.2.0-29-generic')
        self.assertEquals(os.model.name, '#46-Ubuntu')
        self.assertEquals(os.model.family, 'Linux')

