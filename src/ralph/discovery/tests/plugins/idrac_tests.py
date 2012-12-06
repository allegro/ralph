# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from mock import patch
from django.test import TestCase

from ralph.discovery.tests.plugins.samples.idrac import (
    base_info, cpu_info, memory_info, nic_info
)
from ralph.discovery.plugins.idrac import IDRAC, run_idrac
from ralph.discovery.models import (
    Device, IPAddress, Memory, Processor, Ethernet
)


class UnknownIDRACClassException(Exception):
    pass


def patched_run_command(self, class_name, namespace='root/dcim'):
    if class_name == 'DCIM_SystemView':
        return base_info
    elif class_name == 'DCIM_CPUView':
        return cpu_info
    elif class_name == 'DCIM_MemoryView':
        return memory_info
    elif class_name == 'DCIM_NICView':
        return nic_info
    else:
        raise UnknownIDRACClassException()


class IDRACPluginTest(TestCase):
    def setUp(self):
        self.idrac = IDRAC('10.10.10.10')

    @patch('ralph.discovery.plugins.idrac.IDRAC.run_command', patched_run_command)
    def patched_run_idrac_method(self, method):
        return getattr(self.idrac, method)()

    def test_get_base_info(self):
        result = self.patched_run_idrac_method('get_base_info')
        self.assertEqual(
            result,
            {'model': 'PowerEdge R720xd',
             'sn': 'BLSFG5J',
             'manufacturer': 'Dell Inc.'}
        )

    def test_get_ethernets(self):
        result = self.patched_run_idrac_method('get_ethernets')
        self.assertItemsEqual(
            result,
            [
                {
                    'mac': 'BC:30:5B:F1:33:02',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:02'
                },
                {
                    'mac': 'BC:30:5B:F1:33:03',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:03'
                },
                {
                    'mac': 'BC:30:5B:F1:33:00',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:00'
                },
                {
                    'mac': 'BC:30:5B:F1:33:01',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:01'
                }
            ]
        )

    def test_get_cpu(self):
        result = self.patched_run_idrac_method('get_cpu')
        self.assertItemsEqual(
            result,
            [
                {
                    u'socket': 'CPU.Socket.1', u'family': 'B3',
                    u'cores_count': '6',
                    u'model': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    u'speed': '3600', u'manufacturer': 'Intel'
                },
                {
                    u'socket': 'CPU.Socket.2', u'family': 'B3',
                    u'cores_count': '6',
                    u'model': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    u'speed': '3600', u'manufacturer': 'Intel'
                }
            ]
        )

    def test_get_memory(self):
        result = self.patched_run_idrac_method('get_memory')
        self.assertItemsEqual(
            result,
            [
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '3688240E',
                    'socket': 'DIMM.Socket.A1',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '3618240D',
                    'socket': 'DIMM.Socket.A2',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '36A82412',
                    'socket': 'DIMM.Socket.A3',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '36882411',
                    'socket': 'DIMM.Socket.A4',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '363823F2',
                    'socket': 'DIMM.Socket.B1',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '365823F3',
                    'socket': 'DIMM.Socket.B2',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '36B82412',
                    'socket': 'DIMM.Socket.B3',
                    'speed': '1333'
                },
                {
                    'manufacturer': 'Hynix Semiconductor',
                    'model': 'DDR3 DIMM',
                    'size': '8192',
                    'sn': '36482413',
                    'socket': 'DIMM.Socket.B4',
                    'speed': '1333'
                }
            ]
        )

    @patch('ralph.discovery.plugins.idrac.IDRAC.run_command', patched_run_command)
    def test_run_idrac(self):
        run_idrac('10.10.10.10')
        dev = Device.objects.get(sn='BLSFG5J')
        # check memory objects.
        self.assertItemsEqual(
            [(x.model.name, x.label, x.size, x.speed) for x in Memory.objects.filter(
                device=dev)],
            [('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333),
             ('Hynix Semiconductor DDR3 DIMM', 'Hynix Semiconductor DDR3 DIMM',
              8192, 1333)]
        )
        # check ethernet objects.
        self.assertEqual(
            [(x.label, x.mac) for x in Ethernet.objects.filter(device=dev)],
            [('Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:00', u'BC305BF13300'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:01', u'BC305BF13301'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:02', u'BC305BF13302'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:03', u'BC305BF13303')]
        )
        # check processor objects.

