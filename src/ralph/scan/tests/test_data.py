# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import DeviceType, DeviceModel, Device
from ralph.scan.data import get_device_data


class GetDeviceDataTest(TestCase):
    def setUp(self):
        self.device_model = DeviceModel(type=DeviceType.server, name="ziew-X")
        self.device_model.save()
        device = Device(
            model=self.device_model,
            sn='123456789',
            name='ziew',
        )
        device.save()

    def test_basic_data(self):
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['serial_number'], '123456789')
        self.assertEqual(data['hostname'], 'ziew')
        self.assertEqual(data['type'], 'server')
        self.assertEqual(data['model_name'], 'ziew-X')
