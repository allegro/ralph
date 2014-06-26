#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.plugins import ssh_xen
from ralph.discovery import hardware
from ralph.discovery.tests.util import MockSSH


class SshXENPluginTest(TestCase):

    def test_xen_get_macs(self):
        ssh = MockSSH([
            ('sudo xe vif-list params=vm-name-label,MAC', """\
vm-name-label ( RO)    : win2k8
              MAC ( RO): 9a:09:b5:66:31:a9


vm-name-label ( RO)    : win2k8
              MAC ( RO): 8e:b0:fb:7c:c1:00


vm-name-label ( RO)    : Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1
              MAC ( RO): da:e5:24:41:a4:23


""")])
        macs = ssh_xen.get_macs(ssh)
        self.assertEqual(macs, {
            'win2k8': set([
                '9a:09:b5:66:31:a9',
                '8e:b0:fb:7c:c1:00',
            ]),
        })

    def test_xen_get_running_vms(self):
        ssh = MockSSH([
            ('sudo xe vm-list '
             'params=uuid,name-label,power-state,'
             'VCPUs-number,memory-actual', """\
uuid ( RO)             : 66844623-25b9-3d62-f9c9-5efcc35e213f
       name-label ( RW): Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1
      power-state ( RO): halted
    memory-actual ( RO): 0
     VCPUs-number ( RO): 1


uuid ( RO)             : c98c2e2b-a8cf-fe0a-a3c3-2e492c541ef9
       name-label ( RW): win2k8
      power-state ( RO): running
    memory-actual ( RO): 1073713152
     VCPUs-number ( RO): 1


uuid ( RO)             : 4c960326-0522-482f-9213-ffcc3acf8298
       name-label ( RW): Control domain on host: s10820.dc2
      power-state ( RO): running
    memory-actual ( RO): 609222656
     VCPUs-number ( RO): 8


""")])
        vms = ssh_xen.get_running_vms(ssh)
        self.assertEqual(vms, {
            ('win2k8', 'c98c2e2b-a8cf-fe0a-a3c3-2e492c541ef9', 1, 1023)
        })

    def test_xen_disks(self):
        ssh = MockSSH([
            ('sudo xe vm-disk-list '
                'vdi-params=sr-uuid,uuid,virtual-size '
                'vbd-params=vm-name-label,type,device '
                '--multiple', """\
Disk 0 VBD:
vm-name-label ( RO)    : Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1
           device ( RO): xvda
             type ( RW): Disk


Disk 0 VDI:
uuid ( RO)            : bea667bf-deba-44f6-997f-3af9b012ff5e
         sr-uuid ( RO): 9dd5d636-c90a-930d-c04f-897f9624731a
    virtual-size ( RO): 8388608


Disk 0 VBD:
vm-name-label ( RO)    : win2k8
           device ( RO): hda
             type ( RW): Disk


Disk 0 VDI:
uuid ( RO)            : 2150d8e4-d359-4f8b-889d-8dc63668c045
         sr-uuid ( RO): 9dd5d636-c90a-930d-c04f-897f9624731a
    virtual-size ( RO): 25769803776


""")])
        disks = ssh_xen.get_disks(ssh)
        self.maxDiff = None
        self.assertEquals(dict(disks), {
            'win2k8': [
                (
                    '2150d8e4-d359-4f8b-889d-8dc63668c045',
                    '9dd5d636-c90a-930d-c04f-897f9624731a',
                    24576,
                    'hda'
                ),
            ],
            'Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1': [
                (
                    'bea667bf-deba-44f6-997f-3af9b012ff5e',
                    '9dd5d636-c90a-930d-c04f-897f9624731a',
                    8,
                    'xvda'
                ),
            ],
        })

    def test_xen_srs(self):
        ssh = MockSSH([
            ('sudo xe sr-list params=uuid,physical-size,type'             , """\
uuid ( RO)             : 81297512-07a6-4642-715a-fae6500a6cae
    physical-size ( RO): -1
             type ( RO): iso


uuid ( RO)             : b9775958-cedc-8698-a437-2dba4e3653ef
    physical-size ( RO): 0
             type ( RO): udev


uuid ( RO)             : 9dd5d636-c90a-930d-c04f-897f9624731a
    physical-size ( RO): 64768442368
             type ( RO): lvm


uuid ( RO)             : 02afb7d7-670a-2175-5926-9c3b6b0e7651
    physical-size ( RO): -1
             type ( RO): iso


uuid ( RO)             : 9393c492-4311-4dde-9413-75150afdcd97
    physical-size ( RO): 0
             type ( RO): udev


""")])
        srs = ssh_xen.get_srs(ssh)
        self.assertEqual(srs, {
            '9dd5d636-c90a-930d-c04f-897f9624731a': 61768,
        })

    def test_xen_shares(self):
        ssh = MockSSH([
            ("multipath -l", """\
3600144f008bf8a000000500cfff20003 dm-16 OI,COMSTAR
[size=200G][features=1 queue_if_no_path][hwhandler=0][rw]
\_ round-robin 0 [prio=0][active]
\_ 1:0:2:7 sdf 8:80  [active][undef]
\_ 2:0:2:7 sdg 8:96  [active][undef]
3600144f008bf8a000000506429600005 dm-18 OI,COMSTAR
[size=1000G][features=0][hwhandler=0][rw]
\_ round-robin 0 [prio=0][active]
\_ 2:0:2:8 sdi 8:128 [active][undef]
\_ round-robin 0 [prio=0][enabled]
\_ 1:0:2:8 sdh 8:112 [active][undef]
350002ac01add042f dm-4 3PARdata,VV
[size=1000G][features=1 queue_if_no_path][hwhandler=0][rw]
\_ round-robin 0 [prio=0][active]
\_ 1:0:1:0 sdc 8:32  [active][undef]
\_ 2:0:0:0 sdd 8:48  [active][undef]
\_ 1:0:0:0 sdb 8:16  [active][undef]
\_ 2:0:1:0 sde 8:64  [active][undef]
"""),
            ("pvs --noheadings --units M --separator '|'", """\
  /dev/dm-16|VG_XenStorage-e7596296-2426-4a30-66d9-d12b5ba66d52|lvm2|a-|199.99M|604.00M
  /dev/dm-18|VG_XenStorage-d78067e7-5fc3-f684-b512-c4c5a585dce3|lvm2|a-|999.99M|959.90M
  /dev/dm-3|XSLocalEXT-060d5424-b9f1-ad56-629b-10c0c4e2cfa5|lvm2|a-|128.68M|0
  /dev/dm-4|VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052|lvm2|a-|999.99M|108.94M
"""),
            ("lvs --noheadings --units M", """\
                    MGT                                      VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-a-   4.00M
  VHD-0623a1f2-24d8-42e3-bbaa-1d4c8ce24e6a VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  40.09M
  VHD-3db885b1-0d35-47d1-b6e8-a4fe067c0cd4 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  40.09M
  VHD-54b78a6b-d44c-4a6c-9fb4-d7d8d37dde19 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  50.11M
  VHD-5ad6d8d2-0e40-4bb7-8358-1cf5e9a971f3 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  24.05M
  VHD-662ce76e-294d-4a36-b658-8f2d6e7bbd03 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  10.03M
  VHD-776f8031-fce3-4f69-b89e-a00970e249df VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  24.05M
  VHD-8ada0d25-8d72-41a3-94ef-d6a68d829a9f VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-ao  66.39M
  VHD-9557f2c2-7c00-40da-bfa4-5edc7ac4850b VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-ao  29.37M
  VHD-99fe0180-4880-4101-b84d-b38592024128 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  48.94M
  VHD-a91d7e03-bcda-42e1-8d7a-8e9e90557f1b VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-ao  50.11M
  VHD-a9bfce35-9529-43dc-b3b4-0b733f9b2969 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  40.09M
  VHD-c86ad50f-6be7-48ce-afb3-d656ce5a2b7f VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-ao  48.94M
  VHD-cfa5d5e0-7f01-46ee-b3e5-5d78bd58305d VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  45.02M
  VHD-e257aeea-74cb-484d-a454-c4651434b3be VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  39.15M
  VHD-e9d94ff8-8c0e-416c-9c1a-2c94111466f2 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi---  44.04M
  VHD-fabc14ba-e004-4481-a80c-efc11eb8cc00 VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi--- 250.50M
  VHD-fd45752c-342f-4de5-b11d-5da78716ba1a VG_XenStorage-486926cd-e064-61a7-0f8a-9e26c5c50052 -wi-ao  40.09M
  MGT                                      VG_XenStorage-d78067e7-5fc3-f684-b512-c4c5a585dce3 -wi-a-   4.00M
  VHD-03da1032-f25b-4886-8038-5ba774432e37 VG_XenStorage-d78067e7-5fc3-f684-b512-c4c5a585dce3 -wi---  40.09M
  MGT                                      VG_XenStorage-e7596296-2426-4a30-66d9-d12b5ba66d52 -wi-a-   4.00M
  VHD-e4d621b5-a74d-4344-8079-c4d71235648d VG_XenStorage-e7596296-2426-4a30-66d9-d12b5ba66d52 -wi--- 199.39M
  060d5424-b9f1-ad56-629b-10c0c4e2cfa5     XSLocalEXT-060d5424-b9f1-ad56-629b-10c0c4e2cfa5    -wi-ao 128.68M
"""),
        ])
        shares = hardware.get_disk_shares(ssh, include_logical_volumes=True)
        self.maxDiff = None
        self.assertEqual(shares, {
            'MGT': ('600144F008BF8A000000500CFFF20003', 4),
            'VHD-03da1032-f25b-4886-8038-5ba774432e37': (
                '600144F008BF8A000000506429600005', 40),
            'VHD-0623a1f2-24d8-42e3-bbaa-1d4c8ce24e6a': ('50002AC01ADD042F', 40),
            'VHD-3db885b1-0d35-47d1-b6e8-a4fe067c0cd4': ('50002AC01ADD042F', 40),
            'VHD-54b78a6b-d44c-4a6c-9fb4-d7d8d37dde19': ('50002AC01ADD042F', 50),
            'VHD-5ad6d8d2-0e40-4bb7-8358-1cf5e9a971f3': ('50002AC01ADD042F', 24),
            'VHD-662ce76e-294d-4a36-b658-8f2d6e7bbd03': ('50002AC01ADD042F', 10),
            'VHD-776f8031-fce3-4f69-b89e-a00970e249df': ('50002AC01ADD042F', 24),
            'VHD-8ada0d25-8d72-41a3-94ef-d6a68d829a9f': ('50002AC01ADD042F', 66),
            'VHD-9557f2c2-7c00-40da-bfa4-5edc7ac4850b': ('50002AC01ADD042F', 29),
            'VHD-99fe0180-4880-4101-b84d-b38592024128': ('50002AC01ADD042F', 48),
            'VHD-a91d7e03-bcda-42e1-8d7a-8e9e90557f1b': ('50002AC01ADD042F', 50),
            'VHD-a9bfce35-9529-43dc-b3b4-0b733f9b2969': ('50002AC01ADD042F', 40),
            'VHD-c86ad50f-6be7-48ce-afb3-d656ce5a2b7f': ('50002AC01ADD042F', 48),
            'VHD-cfa5d5e0-7f01-46ee-b3e5-5d78bd58305d': ('50002AC01ADD042F', 45),
            'VHD-e257aeea-74cb-484d-a454-c4651434b3be': ('50002AC01ADD042F', 39),
            'VHD-e4d621b5-a74d-4344-8079-c4d71235648d': (
                '600144F008BF8A000000500CFFF20003', 199),
            'VHD-e9d94ff8-8c0e-416c-9c1a-2c94111466f2': ('50002AC01ADD042F', 44),
            'VHD-fabc14ba-e004-4481-a80c-efc11eb8cc00': ('50002AC01ADD042F', 250),
            'VHD-fd45752c-342f-4de5-b11d-5da78716ba1a': ('50002AC01ADD042F', 40)
        })
