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

CHILD1 = {
    'name': 'child_1',
    'barcode': 'ch_001',
    'sn': 'ch-00-00-00-01',
    'model_name': 'xxxx',
    'position': '12',
    'rack': '14',
}

CHILD2 = {
    'name': 'child_2',
    'barcode': 'ch_002',
    'sn': 'ch-00-00-00-02',
    'model_name': 'xxxx',
    'position': '11',
    'rack': '13',
}

CHILD3 = {
    'name': 'child_3',
    'barcode': 'ch_003',
    'sn': 'ch-00-00-00-03',
    'model_name': 'xxxx',
    'position': '13',
    'rack': '13',
}

CHILD4 = {
    'name': 'child_4',
    'barcode': 'ch_004',
    'sn': 'ch-00-00-00-04',
    'model_name': 'xxxx',
    'position': '14',
    'rack': '14',
}

DATACENTER = 'dc1'


class TestDeviceView(TestCase):
    ''' Scenario:
    - test software
    - tests mark as deleted when device has active children
    - tests mark as deleted when device has unactive children
    '''
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
        self.device.name = DEVICE['name']
        self.device.save()
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

        self.child1 = Device.create(
            sn=CHILD1['sn'],
            barcode=CHILD1['barcode'],
            model_name=CHILD1['model_name'],
            model_type=DeviceType.unknown,
            rack=CHILD1['rack'],
            position=CHILD1['position'],
            dc=DATACENTER,
        )
        self.child1.name = CHILD1['name']
        self.child1.save()

        self.child2 = Device.create(
            sn=CHILD2['sn'],
            barcode=CHILD2['barcode'],
            model_name=CHILD2['model_name'],
            model_type=DeviceType.unknown,
            rack=CHILD2['rack'],
            position=CHILD2['position'],
            dc=DATACENTER,
        )
        self.child2.name = CHILD2['name']
        self.child2.save()

        self.child3 = Device.create(
            sn=CHILD3['sn'],
            barcode=CHILD3['barcode'],
            model_name=CHILD3['model_name'],
            model_type=DeviceType.unknown,
            rack=CHILD3['rack'],
            position=CHILD3['position'],
            dc=DATACENTER,
        )
        self.child3.name = CHILD3['name']
        self.child3.save()

        self.child4 = Device.create(
            sn=CHILD4['sn'],
            barcode=CHILD4['barcode'],
            model_name=CHILD4['model_name'],
            model_type=DeviceType.unknown,
            rack=CHILD4['rack'],
            position=CHILD4['position'],
            dc=DATACENTER,
        )
        self.child4.name = CHILD4['name']
        self.child4.save()

    def test_mark_as_deleted_without_children(self):
        device = Device.objects.filter(parent=self.device.id).count()
        self.assertEqual(device, 0)

        url = '/ui/search/info/%s' % self.device.id
        post_data = {
            'name': DEVICE['name'],
            'deleted': True,
            'save_comment': 'deleted',
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        deleted_device = Device.admin_objects.get(id=self.device.id)
        self.assertEqual(deleted_device.deleted, True)

    def test_mark_as_deleted_with_children(self):
        self.child1.parent = self.device
        self.child1.save()

        self.child2.parent = self.device
        self.child2.save()

        self.child3.parent = self.device
        self.child3.save()

        self.child4.parent = self.device
        self.child4.save()

        device = Device.objects.filter(parent=self.device.id).count()
        self.assertEqual(device, 4)

        url = '/ui/search/info/%s' % self.device.id
        post_data = {
            'name': DEVICE['name'],
            'deleted': True,
            'save_comment': 'deleted',
        }
        response = self.client.post(url, post_data)

        deleted_device = Device.admin_objects.get(id=self.device.id)
        self.assertEqual(deleted_device.deleted, False)

        self.assertFormError(
            response, 'form', 'deleted',
            'You can not remove devices that have children.'
        )

    def test_mark_as_deleted_with_deleted_children(self):
        self.child1.parent = self.device
        self.child1.deleted = True
        self.child1.save()

        self.child2.parent = self.device
        self.child2.save()

        self.child3.parent = self.device
        self.child3.save()

        self.child4.parent = self.device
        self.child4.save()

        device = Device.objects.filter(parent=self.device.id).count()
        self.assertEqual(device, 3)

        url = '/ui/search/info/%s' % self.device.id
        post_data = {
            'name': DEVICE['name'],
            'deleted': True,
            'save_comment': 'deleted',
        }
        response = self.client.post(url, post_data)

        deleted_device = Device.admin_objects.get(id=self.device.id)
        self.assertEqual(deleted_device.deleted, False)

        self.assertFormError(
            response, 'form', 'deleted',
            'You can not remove devices that have children.'
        )

        # Delete other childs
        self.child2.parent = self.device
        self.child2.deleted = True
        self.child2.save()

        self.child3.parent = self.device
        self.child3.deleted = True
        self.child3.save()

        self.child4.parent = self.device
        self.child4.deleted = True
        self.child4.save()

        url = '/ui/search/info/%s' % self.device.id
        post_data = {
            'name': DEVICE['name'],
            'deleted': True,
            'save_comment': 'deleted',
        }
        response = self.client.post(url, post_data)

        device = Device.objects.filter(parent=self.device.id).count()
        self.assertEqual(device, 0)

        deleted_device = Device.admin_objects.get(id=self.device.id)
        self.assertEqual(deleted_device.deleted, True)

    def test_software(self):
        url = '/ui/search/software/{}'.format(self.device.id)
        response = self.client.get(url)
        dev = response.context_data['object']
        software = dev.software_set.all()
        self.assertEqual(software[0], self.software1)
        self.assertEqual(software[1], self.software2)
