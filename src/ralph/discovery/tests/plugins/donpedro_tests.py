# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from django.test import TestCase

from ralph.discovery.models import DeviceType, Device, IPAddress, DiskShare
from ralph.discovery.tests.plugins.samples.donpedro import data
from ralph.discovery.api_donpedro import save_device_data


class DonPedroPluginTest(TestCase):
    def setUp(self):
        ip = '10.10.10.10'
        save_device_data(json.loads(data).get('data'), ip)
        self.dev = Device.objects.all()[0]

    def testDev(self):
        self.assertEquals(self.dev.model.name,
            u'Computer System Product Xen 4.1.2')
        self.assertEquals(self.dev.model.get_type_display(),
            'unknown')

    def testProcessors(self):
        processors = self.dev.processor_set.all()
        self.assertTrue(processors[0].speed == processors[1].speed == 2667)
        self.assertTrue(processors[0].cores == processors[1].cores == 1)
        self.assertTrue(processors[0].model.name == processors[1].model.name == '')
        self.assertTrue(processors[0].model.speed == processors[1].model.speed == 2667)
        self.assertTrue(processors[0].model.cores == processors[1].model.cores == 1)
        self.assertTrue(processors[0].speed == processors[1].speed == 2667)

    def testStorage(self):
        storage = self.dev.storage_set.all()
        self.assertEqual(len(storage), 1)
        storage = storage[0]
        self.assertEqual(storage.model.name, 'XENSRC PVDISK SCSI Disk Device 40957MiB')
        self.assertEqual(storage.model.get_type_display(), 'disk drive')
        self.assertEqual(storage.mount_point, 'C:')
        self.assertEqual(storage.label, 'XENSRC PVDISK SCSI Disk Device')
        self.assertEqual(storage.size, 40957)

    def testShares(self):
        pass

    def testOS(self):
        pass
