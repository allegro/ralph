# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from unittest import skip

from ralph.scan.data import get_device_data
from ralph.discovery.models import (
    DeviceType,
    DeviceModel,
    Device,
    Memory,
    Processor,
    ComponentModel,
    ComponentType,
    Storage,
    FibreChannel,
)


class GetDeviceDataTest(TestCase):
    def setUp(self):
        self.device_model = DeviceModel(type=DeviceType.rack_server, name="ziew-X")
        self.device_model.save()
        self.device = Device(
            model=self.device_model,
            sn='123456789',
            name='ziew',
        )
        self.device.save()

    def test_basic_data(self):
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['serial_number'], '123456789')
        self.assertEqual(data['hostname'], 'ziew')
        self.assertEqual(data['type'], 'rack_server')
        self.assertEqual(data['model_name'], 'ziew-X')

    def test_position(self):
        self.device.chassis_position = 3
        self.device.dc = 'dc3'
        self.device.rack='232'
        self.device.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['chassis_position'], 3)
        self.assertEqual(data['data_center'], 'dc3')
        self.assertEqual(data['rack'], '232')

    def test_memory(self):
        for i in xrange(8):
            m = Memory(
                label="ziew",
                size=128,
                device=self.device,
                index=i,
            )
            m.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        memory = data['memory']
        self.assertEqual(len(memory), 8)
        self.assertEqual(memory[0]['label'], "ziew")
        self.assertEqual(memory[0]['size'], 128)
        self.assertEqual(memory[3]['index'], 3)

    def test_processors(self):
        model = ComponentModel(
            type=ComponentType.processor,
            name="CPU Xeon 2533MHz, 4-core",
        )
        model.save()
        for i in xrange(4):
            p = Processor(
                label="ziew",
                model=model,
                device=self.device,
                index=i,
            )
            p.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        processors = data['processors']
        self.assertEqual(len(processors), 4)
        self.assertEqual(processors[0]['label'], "ziew")
        self.assertEqual(processors[0]['model_name'], "CPU Xeon 2533MHz, 4-core")
        self.assertEqual(processors[0]['cores'], 4)
        self.assertEqual(processors[3]['index'], 3)

    def test_disks(self):
        model = ComponentModel(
            type=ComponentType.disk,
            name="HP DG0300BALVP SAS 307200MiB, 10000RPM",
        )
        model.save()
        Storage(
            sn="abc3",
            device=self.device,
            label="ziew",
            mount_point="/dev/hda",
            model=model,
            size=307200,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        disks = data['disks']
        self.assertEqual(len(disks), 1)
        self.assertEqual(disks[0]['size'], 307200)
        self.assertEqual(disks[0]['serial_number'], "abc3")
        self.assertEqual(disks[0]['mount_point'], "/dev/hda")

    @skip('not implemented yet')
    def test_parts(self):
        model = ComponentModel(
            type=ComponentType.fibre,
            name="FC-336",
        )
        model.save
        FibreChannel(
            physical_id='deadbeefcafe',
            label='ziew',
            device=self.device,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        parts = data['parts']
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]['physical_id'], 'deadbeefcafe')
        self.assertEqual(parts[0]['type'], 'fibre')
        self.assertEqual(parts[0]['model_name'], 'FC-336')
