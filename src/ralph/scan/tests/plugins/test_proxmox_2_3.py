# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.util import MockSSH
from ralph.scan.plugins.proxmox_2_3 import (
    _get_node_sn,
    _get_node_mac_address,
    _get_device_info,
    _get_vm_info,
)
from ralph.scan.tests.plugins.samples.proxmox_2_3 import (
    NODE_SN,
    NODE_MAC,
    DEVICE_INFO_SAMPLE,
    VM_INFO_SAMPLE,
)


class Proxmox23PluginTest(TestCase):

    def test_get_node_sn(self):
        ssh = MockSSH([("sudo /usr/sbin/dmidecode -t 1 | grep -i serial", NODE_SN)])
        node_sn = _get_node_sn(ssh)
        node_sn_expected = "XYZ1234567890"
        self.assertEqual(node_sn, node_sn_expected)

    def test_get_node_mac_address(self):
        ssh = MockSSH([("/sbin/ifconfig eth0 | head -n 1", NODE_MAC)])
        node_mac = _get_node_mac_address(ssh)
        node_mac_expected = "202020202020"
        self.assertEqual(node_mac, node_mac_expected)

    def test_get_device_info(self):
        ssh = MockSSH([
            ("sudo /usr/bin/pvesh get /nodes/node123/status", DEVICE_INFO_SAMPLE)
        ])
        node_name, session, base_url = 'node123', None, None
        device_info = _get_device_info(node_name, session, ssh, base_url)
        device_info_expected = {
            u'installed_software': [{
                u'model_name': u'Proxmox',
                u'path': u'proxmox',
            }],
            u'model_name': u'Proxmox',
            u'processors': [{
                u'cores': 16,
                u'family': u'Intel(R) Xeon(R) CPU F7-666 0 @ 2.00GHz',
                u'label': u'CPU 1',
                u'speed': 2000
            }, {
                u'cores': 16,
                u'family': u'Intel(R) Xeon(R) CPU F7-666 0 @ 2.00GHz',
                u'label': u'CPU 2',
                u'speed': 2000
            }]
        }
        self.assertEqual(device_info, device_info_expected)

    def test_vm_info(self):
        ssh = MockSSH([
            ("sudo /usr/bin/pvesh get /nodes/node123/qemu/vm123/config", VM_INFO_SAMPLE)
        ])
        node_name, vmid, session, base_url = 'node123', 'vm123', None, None
        vm_info = _get_vm_info(node_name, vmid, session, ssh, base_url)
        vm_info_expexted = {
            u'disks': [{
                u'family': u'Proxmox Virtual Disk',
                u'label': u'vm-0123456-disk-1',
                u'model_name': u'Proxmox Virtual Disk 8192MiB',
                u'size': 8192
            }],
            u'hostname': u'test_node.local',
            u'mac_addresses': [u'101010101010'],
            u'memory': [{
                u'index': 0,
                u'label': u'Virtual DIMM 0',
                u'size': 1024
            }],
            u'model_name': u'Proxmox qemu kvm',
            u'processors': [{
                u'cores': 1,
                u'family': u'QEMU Virtual',
                u'index': 1,
                u'label': u'CPU 1',
                u'model_name': u'QEMU Virtual CPU'
            }],
            u'type': u'virtual server'
        }
        self.assertEqual(vm_info, vm_info_expexted)
