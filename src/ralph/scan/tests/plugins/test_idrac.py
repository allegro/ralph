# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from mock import Mock
from xml.etree import cElementTree as ET

from ralph.scan.tests.plugins.samples import idrac as idrac_samples
from ralph.scan.plugins.idrac import (
    IDRAC,
    _get_base_info,
    _get_disks,
    _get_fibrechannel_cards,
    _get_mac_addresses,
    _get_memory,
    _get_processors,
)


SAMPLES_MAPPER = {
    'DCIM_SystemView': 'base_info',
    'DCIM_CPUView': 'cpu_info',
    'DCIM_MemoryView': 'memory_info',
    'DCIM_NICView': 'nic_info',
    'DCIM_PhysicalDiskView': 'physical_disk_info',
    'DCIM_PCIDeviceView': 'pci_info',
}


class IdracPluginTest(TestCase):

    def setUp(self):
        self.idrac_manager = IDRAC('127.0.0.1', 'test', 'test')

        def side_effect(class_name, selector='root/dcim'):
            return ET.XML(getattr(idrac_samples, SAMPLES_MAPPER[class_name]))
        self.idrac_manager.run_command = Mock(side_effect=side_effect)

    def test_get_base_info(self):
        self.assertEquals(
            _get_base_info(self.idrac_manager),
            {
                'model_name': 'Dell PowerEdge R720xd',
                'serial_number': 'AMSFG5J',
            },
        )

    def test_get_mac_addresses(self):
        self.assertEquals(
            _get_mac_addresses(self.idrac_manager),
            [
                'BC30FBF13302',
                'BC30FBF13303',
                'BC30FBF13300',
                'BC30FBF13301',
            ],
        )

    def test_get_processors(self):
        self.assertEquals(
            _get_processors(self.idrac_manager),
            [
                {
                    'cores': '6',
                    'family': 'B3',
                    'index': 1,
                    'label': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'model_name': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'speed': '3600',
                },
                {
                    'cores': '6',
                    'family': 'B3',
                    'index': 2,
                    'label': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'model_name': 'Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz',
                    'speed': '3600',
                },
            ],
        )

    def test_get_memory(self):
        self.assertEquals(
            _get_memory(self.idrac_manager),
            [
                {
                    'index': 1,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 2,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 3,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 4,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 5,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 6,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 7,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
                {
                    'index': 8,
                    'label': 'Hynix Semiconductor DDR3 DIMM',
                    'size': '8192',
                    'speed': '1333',
                },
            ],
        )

    def test_get_disks(self):
        self.assertEquals(
            _get_disks(self.idrac_manager),
            [
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1E32KSCNJ',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1E32KTYEA',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1C5202177',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1E32KUDHD',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1C5201540',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1C5200178',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1C5200307',
                    'size': 278,
                },
                {
                    'family': 'WD',
                    'label': 'WD WD3001BKHG',
                    'model_name': 'WD WD3001BKHG',
                    'serial_number': 'ABC1CC1J7098',
                    'size': 278,
                },
            ],
        )

    def test_get_fibrechannel_cards(self):
        self.assertEquals(
            _get_fibrechannel_cards(self.idrac_manager),
            [
                {
                    u'label': ' Saturn-X: LightPulse Fibre Channel Host Adapter',
                    u'physical_id': '6',
                },
                {
                    u'label': ' Saturn-X: LightPulse Fibre Channel Host Adapter',
                    u'physical_id': '4',
                },
            ],
        )
