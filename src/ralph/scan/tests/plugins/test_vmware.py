# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.scan.plugins.vmware import _get_vm_info
from ralph.scan.tests.plugins.samples.vmware import (
    VMWARE_SAMPLE,
    VMWARE_SAMPLE_SUBDEV_NO_MAC,
)


class VMWarePluginTest(TestCase):

    def test_get_vm_info(self):
        result = _get_vm_info(VMWARE_SAMPLE, [])
        self.assertEqual(
            result,
            {
                u'disks': [
                    {
                        u'family': 'VMWare Virtual Disk',
                        u'label': 'Hard disk 1',
                        u'size': 276480,
                    },
                ],
                u'hostname': 'app-1.internal',
                u'mac_addresses': ['002233CCBBAA'],
                u'memory': [{u'label': u'Virtual RAM', u'size': 194560}],
                u'model_name': 'VMWare Virtual Server',
                u'processors': [
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 0,
                        u'label': u'Virtual CPU 0'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 1,
                        u'label': u'Virtual CPU 1'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 2,
                        u'label': u'Virtual CPU 2'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 3,
                        u'label': u'Virtual CPU 3'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 4,
                        u'label': u'Virtual CPU 4'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 5,
                        u'label': u'Virtual CPU 5'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 6,
                        u'label': u'Virtual CPU 6'
                    },
                    {
                        u'cores': 1,
                        u'family': u'Virtual CPU',
                        u'index': 7,
                        u'label': u'Virtual CPU 7'
                    }
                ],
                u'system_ip_addresses': ['10.10.10.11'],
                u'system_label': 'Microsoft Windows Server 2008 R2 (64-bit)',
                u'type': u'virtual server'
            }
        )

    def test_get_vm_info_subdev_no_mac(self):
        """Subdevice without a MAC address should return None."""
        result = _get_vm_info(VMWARE_SAMPLE_SUBDEV_NO_MAC, [])
        self.assertEqual(result, None)
