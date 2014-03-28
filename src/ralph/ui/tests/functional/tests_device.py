# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from ralph.ui.tests.global_utils import login_as_su
from ralph.discovery.models import Device, DeviceType
from ralph.discovery.models_component import Software


DEVICE = {
    'name': 'SimpleDevice',
    'ip': '10.0.0.1',
    'remarks': 'Very important device',
    'venture': 'SimpleVenture',
    'ventureSymbol': 'simple_venture',
    'venture_role': 'VentureRole',
    'model_name': 'xxxx',
    'position': '12',
    'rack': '14',
    'barcode': 'bc_dev',
    'sn': '0000000001',
    'mac': '00:00:00:00:00:00',
}

DATACENTER = 'dc1'


class DeviceViewTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.device = Device.create(
            sn=DEVICE['sn'],
            barcode=DEVICE['barcode'],
            remarks=DEVICE['remarks'],
            model_name=DEVICE['model_name'],
            model_type=DeviceType.unknown,
            rack=DEVICE['rack'],
            position=DEVICE['position'],
            dc=DATACENTER,
        )
        self.software1 = Software.create(
            dev=self.device,
            path='apache2',
            model_name='apache2 2.4.3',
            label='apache',
            family='http servers',
            version='2.4.3',
            priority=69,
        )
        self.software2 = Software.create(
            dev=self.device,
            path='gcc',
            model_name='gcc 4.7.2',
            label='gcc',
            family='compilers',
            version='4.7.2',
            priority=69,
        )

    def test_software(self):
        url = '/ui/search/software/{}'.format(self.device.id)
        response = self.client.get(url, follow=False)
        dev = response.context_data['object']
        software = dev.software_set.all()
        self.assertEqual(software[0], self.software1)
        self.assertEqual(software[1], self.software2)
