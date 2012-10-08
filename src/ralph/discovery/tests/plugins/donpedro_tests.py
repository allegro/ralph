# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from django.test import TestCase

from ralph.discovery.models import Device, DiskShare, DiskShareMount
from ralph.discovery.tests.plugins.samples.donpedro import data
from ralph.discovery.api_donpedro import save_device_data


class DonPedroPluginTest(TestCase):
    def setUp(self):
        ip = '10.10.10.10'
        save_device_data(json.loads(data).get('data'), ip)
        self.dev = Device.objects.all()[0]
        d = DiskShare(device=self.dev)
        d.wwn = '25D304C1'
        d.save()
        # once again - check for duplicates also
        save_device_data(json.loads(data).get('data'), ip)
        self.total_memory_size = 3068
        self.total_storage_size = 40957
        self.total_cores_count = 2

    def testDev(self):
        self.assertEquals(
            self.dev.model.name, u'Computer System Product Xen 4.1.2')
        self.assertEquals(
            self.dev.model.get_type_display(), 'unknown')

    def testProcessors(self):
        processors = self.dev.processor_set.all()
        self.assertTrue(processors[0].speed == processors[1].speed == 2667)
        self.assertTrue(processors[0].cores == processors[1].cores == 1)
        self.assertTrue(
            processors[0].model.name == processors[1].model.name ==
            u'CPU Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz 2667Mhz multicore'
        )
        self.assertTrue(
            processors[0].model.speed == processors[1].model.speed == 2667
        )
        self.assertTrue(
            processors[0].model.cores == processors[1].model.cores == 1)

    def testStorage(self):
        storage = self.dev.storage_set.all()
        self.assertEqual(len(storage), 1)
        storage = storage[0]
        self.assertEqual(
            storage.model.name, 'XENSRC PVDISK SCSI Disk Device 40957MiB')
        self.assertEqual(storage.model.get_type_display(), 'disk drive')
        self.assertEqual(storage.mount_point, 'C:')
        self.assertEqual(storage.label, 'XENSRC PVDISK SCSI Disk Device')
        self.assertEqual(storage.size, 40957)

    def testFC(self):
        fc = self.dev.fibrechannel_set.all()
        self.assertEqual(len(fc), 2)
        self.assertEqual(
            fc[0].model.name, u'QMH2462')
        self.assertEqual(
            fc[1].model.name, u'QMH2462')
        self.assertTrue(
            fc[0].label == fc[1].label == u'QLogic QMH2462 Fibre Channel Adapter')

    def testMemory(self):
        memory = self.dev.memory_set.all()
        self.assertEqual(len(memory), 1)
        memory = memory[0]
        self.assertEqual(memory.size, 3068)
        self.assertEqual(memory.label, 'RAM 3068MiB')
        self.assertEqual(memory.model.speed, 0)
        self.assertEqual(memory.model.name, 'RAM Windows 3068MiB')
        self.assertEqual(memory.model.size, self.total_memory_size)
        self.assertEqual(memory.model.family, '')

    def testOS(self):
        os = self.dev.operatingsystem_set.all()
        self.assertEqual(len(os), 1)
        os = os[0]
        # unfortunatelly additional space is being added to the os.label
        self.assertEqual(
            os.label, 'Microsoft Windows Server 2008 R2 Standard '
        )
        self.assertEqual(os.model.name, 'Microsoft Windows Server 2008 R2 Standard')
        self.assertEqual(os.memory, 3067)
        self.assertEqual(os.model.family, 'Windows')
        self.assertEqual(os.storage, self.total_storage_size)
        self.assertEqual(os.cores_count, self.total_cores_count)

    def testShares(self):
        # only first share mount created, because DiskShare is presetn
        self.assertEqual(DiskShareMount.object.count(), 1)
        self.assertEqual(DiskShareMount.objects.all()[0].share.wwn, '25D304C1')
