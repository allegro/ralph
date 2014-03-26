# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from django.test import TestCase

from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    Device,
    DeviceType,
    DiskShare,
    DiskShareMount,
    Software,
    Storage,
)
from ralph.discovery.tests.plugins.samples.donpedro import (
    data,
    incomplete_data,
    no_eth_data,
)
from ralph.discovery.api_donpedro import (
    NoRequiredDataError,
    NoRequiredIPAddressError,
    save_device_data,
    save_storage,
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
        # prepare storage special cases
        self._prepare_storage_special_cases()

    def _prepare_storage_special_cases(self):
        self.special_dev = Device.create(
            sn='sn_123_321_123_321',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        self.temp_dev = Device.create(
            sn='sn_999_888_777',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        model_name = 'TestStorage 40960MiB'
        model, _ = ComponentModel.create(
            type=ComponentType.disk,
            priority=0,
            size=40960,
            family=model_name,
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='C:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='D:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_2',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='E:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_3',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.temp_dev,
            mount_point='G:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_5',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='H:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_6',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='X:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_7',
            },
        )
        # FIXME: this assigns a 40GB model to a 80GB device. How to handles
        # cases like this?
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='I:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 81920,
                'sn': 'stor_sn_123_321_8',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            device=self.special_dev,
            mount_point='Y:',
            defaults={
                'label': 'TestStorage',
                'model': model,
                'size': 40960,
                'sn': 'stor_sn_123_321_9',
            },
        )
        storage, _ = Storage.concurrent_get_or_create(
            sn='stor_sn_123_321_10',
            defaults={
                'device': self.special_dev,
                'label': 'TestStorage',
                'model': model,
                'size': 81920,
            },
        )
        save_storage(
            [
                {
                    'sn': 'stor_sn_123_321_1',
                    'mountpoint': 'C:',
                    'label': 'TestStorage',
                    'size': 40960,
                },
                {
                    'sn': 'stor_sn_123_321_2',
                    'mountpoint': 'D:',
                    'label': 'TestStorage',
                    'size': 40960,

                },
                {
                    'sn': 'stor_sn_123_321_4',
                    'mountpoint': 'F:',
                    'label': 'TestStorage',
                    'size': 40960
                },
                {
                    'sn': 'stor_sn_123_321_5',
                    'mountpoint': 'G:',
                    'label': 'TestStorage',
                    'size': 40960
                },
                {
                    'sn': 'stor_sn_123_321_7',
                    'mountpoint': 'H:',
                    'label': 'TestStorage',
                    'size': 40960
                },
                {
                    'sn': 'stor_sn_123_321_9',
                    'mountpoint': 'I:',
                    'label': 'TestStorage',
                    'size': 81920
                },
                {
                    'sn': 'stor_sn_123_321_10',
                    'mountpoint': 'J:',
                    'label': 'TestStorage',
                    'size': 40960
                }
            ],
            self.special_dev
        )

    def test_dev(self):
        self.assertEquals(
            self.dev.model.name,
            u'Computer System Product Xen 4.1.2'
        )
        self.assertEquals(
            self.dev.model.get_type_display(),
            'unknown'
        )
        self.assertEquals(
            self.dev.ipaddress_set.all()[0].address,
            '10.100.0.10'
        )

    def test_processors(self):
        processors = self.dev.processor_set.all()
        self.assertEquals(processors[0].speed, processors[1].speed)
        self.assertEquals(processors[0].speed, 2667)
        self.assertEquals(processors[0].cores, processors[1].cores)
        self.assertEquals(processors[0].cores, 1)
        self.assertTrue(
            processors[0].model.name == processors[1].model.name ==
            u'CPU Virtual Intel(R) Xeon(R) CPU           E5640  '
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
            storage.model.name,
            'XENSRC PVDISK SCSI Disk Device 40957MiB 40957MiB'
        )
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
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                mount_point='D:',
                sn='stor_sn_123_321_2',
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_3',
                mount_point__isnull=True
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_4',
                mount_point='F:',
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_5',
                mount_point='G:',
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_6',
                mount_point__isnull=True
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_7',
                mount_point='H:',
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_8',
                mount_point='I:',
                size=81920,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_9',
                mount_point__isnull=True,
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertFalse(
            self.special_dev.storage_set.filter(
                mount_point='J:',
                size=40960,
                label='TestStorage'
            ).exists()
        )
        self.assertTrue(
            self.special_dev.storage_set.filter(
                sn='stor_sn_123_321_10',
                mount_point__isnull=True,
                size=81920,
                label='TestStorage'
            ).exists()
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
        self.assertEqual(memory.model.family, 'Windows')

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
        with self.assertRaises(NoRequiredDataError):
            save_device_data(json.loads(incomplete_data).get('data'),
                             '20.20.20.20')

    def test_no_eth_device_creation(self):
        with self.assertRaises(NoRequiredIPAddressError):
            save_device_data(
                json.loads(no_eth_data).get('data'),
                '30.30.30.30'
            )

    def test_software(self):
        self.assertTrue(Software.objects.count(), 2)
        self.assertEquals(Software.objects.all()[0].version, "1.2.33")
        self.assertEquals(Software.objects.all()[1].version, "0.8.99")
