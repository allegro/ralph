# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import json
from django.test import TestCase

from ralph.discovery.models import (
    Device, DiskShare, DiskShareMount, DeviceType, Storage, ComponentModel,
    ComponentType
)
from ralph.discovery.tests.plugins.samples.donpedro import (
    data, incomplete_data, no_eth_data
)
from ralph.discovery.api_donpedro import (
    save_device_data, NoRequiredDataError, save_storage
)


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
        # create device to test special cases
        self.special_dev = Device.create(
            sn='sn_123_321_123_321',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        model_name = 'TestStorageModel'
        model, _ = ComponentModel.concurrent_get_or_create(
            size=40960, type=ComponentType.disk, speed=0, cores=0,
            extra='', extra_hash=hashlib.md5('').hexdigest(),
            family=model_name
        )
        model.name = model_name
        model.save()
        incomplete_storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='C:'
        )
        incomplete_storage.label = 'TestStorage1'
        incomplete_storage.size = 40960
        incomplete_storage.model = model
        incomplete_storage.save()
        normal_storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='D:'
        )
        normal_storage.label = 'TestStorage2'
        normal_storage.size = 40960
        normal_storage.model = model
        normal_storage.sn = 'stor_sn_123_321_2'
        normal_storage.save()
        to_del_storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='E:'
        )
        to_del_storage.label = 'TestStorage3'
        to_del_storage.size = 40960
        to_del_storage.model = model
        to_del_storage.save()
        save_storage(
            [
                {
                    'sn': 'stor_sn_123_321_1',
                    'mountpoint': 'C:',
                    'label': 'TestStorage1',
                    'size': '40960',
                },
                {
                    'sn': 'stor_sn_123_321_2',
                    'mountpoint': 'D:',
                    'label': 'TestStorage2',
                    'size': '40960',

                }
            ],
            self.special_dev
        )

    def test_dev(self):
        self.assertEquals(
            self.dev.model.name, u'Computer System Product Xen 4.1.2')
        self.assertEquals(
            self.dev.model.get_type_display(), 'unknown')

    def test_processors(self):
        processors = self.dev.processor_set.all()
        self.assertEquals(processors[0].speed, processors[1].speed)
        self.assertEquals(processors[0].speed, 2667)
        self.assertEquals(processors[0].cores, processors[1].cores)
        self.assertEquals(processors[0].cores, 4)
        self.assertTrue(
            processors[0].model.name == processors[1].model.name ==
            u'CPU Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz 2667Mhz'
        )
        self.assertTrue(
            processors[0].model.speed == processors[1].model.speed == 2667
        )
        self.assertTrue(
            processors[0].model.cores == processors[1].model.cores == 1)

    def test_storage(self):
        storage = self.dev.storage_set.all()
        self.assertEqual(len(storage), 1)
        storage = storage[0]
        self.assertEqual(
            storage.model.name, 'XENSRC PVDISK SCSI Disk Device 40957MiB')
        self.assertEqual(storage.model.get_type_display(), 'disk drive')
        self.assertEqual(storage.mount_point, 'C:')
        self.assertEqual(storage.label, 'XENSRC PVDISK SCSI Disk Device')
        self.assertEqual(storage.size, 40957)
        self.assertEqual(storage.sn, '03da1030-f25b-47')

    def test_storage_special_cases(self):
        self.assertTrue(
            self.special_dev.storage_set.filter(
                mount_point='C:',
                sn='stor_sn_123_321_1',
                size=40960,
                label='TestStorage1'
            )
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                mount_point='D:',
                sn='stor_sn_123_321_2',
                size=40960,
                label='TestStorage2'
            )
        )
        self.assertFalse(
            self.special_dev.storage_set.filter(mount_point='E:').exists()
        )

    def test_fc(self):
        fc = self.dev.fibrechannel_set.all()
        self.assertEqual(len(fc), 2)
        self.assertEqual(
            fc[0].model.name, u'QMH2462')
        self.assertEqual(
            fc[1].model.name, u'QMH2462')
        self.assertTrue(
            fc[0].label == fc[1].label ==
            u'QLogic QMH2462 Fibre Channel Adapter')

    def test_memory(self):
        memory = self.dev.memory_set.all()
        self.assertEqual(len(memory), 1)
        memory = memory[0]
        self.assertEqual(memory.size, 3068)
        self.assertEqual(memory.label, 'RAM 3068MiB')
        self.assertEqual(memory.model.speed, 0)
        self.assertEqual(memory.model.name, 'RAM Windows 3068MiB')
        self.assertEqual(memory.model.size, self.total_memory_size)
        self.assertEqual(memory.model.family, '')

    def test_os(self):
        os = self.dev.operatingsystem_set.all()
        self.assertEqual(len(os), 1)
        os = os[0]
        # unfortunatelly additional space is being added to the os.label
        self.assertEqual(
            os.label, 'Microsoft Windows Server 2008 R2 Standard '
        )
        self.assertEqual(
            os.model.name, 'Microsoft Windows Server 2008 R2 Standard')
        self.assertEqual(os.memory, 3067)
        self.assertEqual(os.model.family, 'Windows')
        self.assertEqual(os.storage, self.total_storage_size)
        self.assertEqual(os.cores_count, self.total_cores_count)

    def test_shares(self):
        # only first share mount created, because DiskShare is presetn
        self.assertEqual(DiskShareMount.objects.count(), 1)
        self.assertEqual(DiskShareMount.objects.all()[0].share.wwn, '25D304C1')

    def test_incomplete_data_handling(self):
        with self.assertRaises(NoRequiredDataError) as cm:
            save_device_data(json.loads(incomplete_data).get('data'),
                             '20.20.20.20')
        self.assertEqual(cm.exception.message,
                         'No MAC addresses and no device SN.')

    def test_no_eth_device_creation(self):
        save_device_data(json.loads(no_eth_data).get('data'),
                         '30.30.30.30')
        self.assertEqual(
            Device.objects.filter(
                sn='7ddaaa4a-dc00-de38-e683-da037fd729ac').count(), 1)

