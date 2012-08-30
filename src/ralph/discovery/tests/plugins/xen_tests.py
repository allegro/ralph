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
                ('sudo xe vm-list params=uuid,name-label,power-state', """\
uuid ( RO)           : 66844623-25b9-3d62-f9c9-5efcc35e213f
     name-label ( RW): Transfer VM for VDI 07f1cca1-056d-4694-879e-adcb2ed989e1
    power-state ( RO): halted


uuid ( RO)           : c98c2e2b-a8cf-fe0a-a3c3-2e492c541ef9
     name-label ( RW): win2k8
    power-state ( RO): running


uuid ( RO)           : 4c960326-0522-482f-9213-ffcc3acf8298
     name-label ( RW): Control domain on host: s10820.dc2
    power-state ( RO): running


""")])
        vms = ssh_xen.get_running_vms(ssh)
        self.assertEqual(vms, {
            ('win2k8', '66844623-25b9-3d62-f9c9-5efcc35e213f')
        })
