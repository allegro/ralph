#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.plugins import ssh_xen
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
            ('win2k8', 'c98c2e2b-a8cf-fe0a-a3c3-2e492c541ef9', 1, 1048548)
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
                    25165824,
                    'hda'
                ),
            ],
            'Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1': [
                (
                    'bea667bf-deba-44f6-997f-3af9b012ff5e',
                    '9dd5d636-c90a-930d-c04f-897f9624731a',
                    8192,
                    'xvda'
                ),
            ],
        })

    def test_xen_srs(self):
        ssh = MockSSH([
            ('sudo xe sr-list params=uuid,physical-size,type'
            , """\
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
            '9dd5d636-c90a-930d-c04f-897f9624731a': 63250432,
        })
