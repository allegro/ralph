# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from mock import patch
from django.test import TestCase

from ralph.discovery.tests.plugins.samples.idrac import (
    base_info, cpu_info, memory_info, nic_info, physical_disk_info,
    pci_info
)
from ralph.discovery.plugins.idrac import IDRAC, run_idrac
from ralph.discovery.models import (
    Device, IPAddress, Memory, Processor, Ethernet,
    FibreChannel, Storage
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
    elif class_name == 'DCIM_PhysicalDiskView':
        return physical_disk_info
    elif class_name == 'DCIM_PCIDeviceView':
        return pci_info
    else:
        raise UnknownIDRACClassException()


class IDRACPluginTest(TestCase):

    def setUp(self):
        self.idrac = IDRAC('10.10.10.10')

    @patch(
        'ralph.discovery.plugins.idrac.IDRAC.run_command', patched_run_command)
    def patched_run_idrac_method(self, method):
        return getattr(self.idrac, method)()

    def test_get_base_info(self):
        result = self.patched_run_idrac_method('get_base_info')
        self.assertEqual(
            result,
            {'model': 'PowerEdge R720xd',
             'sn': 'AMSFG5J',
             'manufacturer': 'Dell Inc.'}
        )

    def test_get_ethernets(self):
        result = self.patched_run_idrac_method('get_ethernets')
        self.assertItemsEqual(
            result,
            [
                {
                    'mac': 'BC:30:FB:F1:33:02',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - '
                    'BC:30:FB:F1:33:02'
                },
                {
                    'mac': 'BC:30:FB:F1:33:03',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - '
                    'BC:30:FB:F1:33:03'
                },
                {
                    'mac': 'BC:30:FB:F1:33:00',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - '
                    'BC:30:FB:F1:33:00'
                },
                {
                    'mac': 'BC:30:FB:F1:33:01',
                    'label': 'Intel(R) Gigabit 4P I350-t rNDC - '
                    'BC:30:FB:F1:33:01'
                }
            ]
        )

    def test_get_cpu(self):
        result = self.patched_run_idrac_method('get_cpu')
        self.assertItemsEqual(
            result,
            [
                {
                    'socket': 'CPU.Socket.1', u'family': 'B3',
                    'cores_count': '6',
                    'model': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'speed': '3600', u'manufacturer': 'Intel'
                },
                {
                    'socket': 'CPU.Socket.2', u'family': 'B3',
                    'cores_count': '6',
                    'model': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'speed': '3600', u'manufacturer': 'Intel'
                }
            ]
        )

    def test_get_storage(self):
        result = self.patched_run_idrac_method('get_storage')
        self.assertItemsEqual(
            result,
            [
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1E32KSCNJ',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1E32KTYEA',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1C5202177',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1E32KUDHD',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1C5201540',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1C5200178',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1C5200307',
                },
                {
                    'manufacturer': 'WD',
                    'model': 'WD3001BKHG',
                    'size': '299439751168',
                    'sn': 'ABC1CC1J7098',
                }
            ]
        )

    def test_get_fc_cards(self):
        result = self.patched_run_idrac_method('get_fc_cards')
        self.assertItemsEqual(
            result,
            [
                {
                    'label': ' Saturn-X: LightPulse Fibre Channel '
                    'Host Adapter',
                    'physical_id': '6',
                },
                {
                    'label': ' Saturn-X: LightPulse Fibre Channel '
                    'Host Adapter',
                    'physical_id': '4',
                }
            ])

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

    @patch(
        'ralph.discovery.plugins.idrac.IDRAC.run_command', patched_run_command)
    def test_run_idrac(self):
        """Now, black-box test - run_idrac method which creates device data
        and check resulting them all here.
        """
        run_idrac('10.10.10.10')
        dev = Device.objects.get(sn='AMSFG5J')
        # check memory objects.
        self.assertItemsEqual(
            [(mem.model.name, mem.label, mem.size, mem.speed)
                for mem in Memory.objects.filter(
                    device=dev)],
            [(
                'RAM  8192MiB, 1333MHz',
                'Hynix Semiconductor DDR3 DIMM',
                8192,
                1333,
            )] * 8,
        )
        # check ethernet objects.
        self.assertItemsEqual(
            [(eth.label, eth.mac) for eth in Ethernet.objects.filter(
                device=dev)],
            [('Intel(R) Gigabit 4P I350-t rNDC - BC:30:FB:F1:33:00',
              'BC30FBF13300'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:FB:F1:33:01',
              'BC30FBF13301'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:FB:F1:33:02',
              'BC30FBF13302'),
             ('Intel(R) Gigabit 4P I350-t rNDC - BC:30:FB:F1:33:03',
              'BC30FBF13303')]
        )
        # check processor objects.
        self.assertItemsEqual(
            [(pr.index, pr.speed, pr.cores,
              pr.model.name, pr.model.family, pr.model.cores,
              pr.model.type, pr.cores)
                for pr in Processor.objects.filter(device=dev)],
            [
                (
                    1,
                    3600,
                    6,
                    'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'B3',
                    6,
                    1,
                    6
                ), (
                    2,
                    3600,
                    6,
                    'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'B3',
                    6,
                    1,
                    6
                )
            ]
        )
        # should have Fibre Channel objects as well.
        self.assertItemsEqual(
            [(fc.label, fc.model.name,
              fc.model.size, fc.model.type,
              fc.model.speed, fc.model.cores)
                for fc in FibreChannel.objects.filter(device=dev)],
            [(' Saturn-X: LightPulse Fibre Channel Host Adapter',
              ' Saturn-X: LightPulse Fibre Channel Host Adapter',
              0,
              6,
              0,
              0),
             (' Saturn-X: LightPulse Fibre Channel Host Adapter',
              ' Saturn-X: LightPulse Fibre Channel Host Adapter',
              0,
              6,
              0,
              0)]
        )

        # should have Storage created for the device.
        storage_result = [
            (st.label, fc.model.name,
             fc.model.size, fc.model.type,
             fc.model.speed, fc.model.cores)
            for st in Storage.objects.filter(device=dev)
        ]
        storage_data = [
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0),
            ('WD WD3001BKHG 278MiB',
             ' Saturn-X: LightPulse Fibre Channel Host Adapter',
             0,
             6,
             0,
             0)]
        self.assertItemsEqual(
            storage_result,
            storage_data
        )
        # finally, check ip managment address.
        ip = IPAddress.objects.get(device=dev)
        self.assertTrue(ip.is_management)
        self.assertEqual(ip.address, '10.10.10.10')
