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
    _get_base_info,
    IDRAC,
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
            {'model_name': 'Dell PowerEdge R720xd', 'sn': 'AMSFG5J'},
        )

#import pprint
#pprint.pprint(_get_base_info(self.idrac_manager))

