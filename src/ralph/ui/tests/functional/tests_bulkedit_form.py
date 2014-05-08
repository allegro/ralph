# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from django.test import TestCase
from ralph.business.models import Venture, VentureRole
from ralph.discovery.models_device import (
    Device,
    DeviceType,
    DeprecationKind,
    MarginKind,
)
from ralph.discovery.models_history import HistoryChange
from ralph.ui.tests.global_utils import login_as_su

DATACENTER = 'dc1'
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
DEVICE2 = {
    'name': 'SimpleDevice 2',
    'ip': '10.0.0.2',
    'remarks': 'Very important device 2',
    'venture': 'SimpleVenture',
    'ventureSymbol': 'simple_venture',
    'venture_role': 'VentureRole',
    'model_name': 'xxxx',
    'position': '13',
    'rack': '14',
    'barcode': 'bc_dev2',
    'sn': '0000000002',
    'mac': '00:00:00:00:00:01',
}
ERROR_MSG = {
    'no_mark_fields': 'Please mark changed fields.',
    'empty_save_comment': 'Please correct the errors.',
    'empty_save_comment_field': 'You must describe your change',
}


class BulkeditTest(TestCase):

    """ Tests edit form

    Scenario:
    1. Changes data in single device + test history change
    2. Changes data in more than one device
    3. Send form without select edit fields
    4. Send form with empty save comment field
    5. If data was added, check depreciation_date
    """

    def setUp(self):
        self.client = login_as_su()

        self.deprecation_kind = DeprecationKind(months=24, remarks='Default')
        self.deprecation_kind.save()

        self.margin = MarginKind(margin=100, remarks='100%')
        self.margin.save()

        self.venture = Venture(name='VenureName')
        self.venture.save()

        self.role = VentureRole(venture=self.venture, name='VentureRole')
        self.role.save()

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

        self.device2 = Device.create(
            sn=DEVICE2['sn'],
            barcode=DEVICE2['barcode'],
            remarks=DEVICE2['remarks'],
            model_name=DEVICE2['model_name'],
            model_type=DeviceType.unknown,
            rack=DEVICE2['rack'],
            position=DEVICE2['position'],
            dc=DATACENTER,
        )
        self.device2.name = DEVICE2['name']
        self.device2.save()

    def test_single_device_edit(self):
        url = '/ui/search/bulkedit/'

        text_fields = ('position', 'chassis_position', 'remarks', 'verified')
        device_fields = []
        device_fields.extend(text_fields)


        post_data = {
            'select': [self.device.id],  # 1
            'edit': device_fields,
            'verified': True,
            'position': '9',
            'chassis_position': 10,
            'remarks': 'Hello Ralph',
            'save_comment': 'Everything has changed',
            'save': '',  # save form
        }
        self.client.post(url, post_data)

        # Check if data from form is the same that data in database
        device = Device.objects.get(id=self.device.id)
        for field in device_fields:
            db_data = getattr(device, field)
            form_data = post_data[field]
            msg = 'FIELD: %s, DB: %s FORM: %s' % (field, db_data, form_data)
            self.assertEqual(unicode(db_data), unicode(form_data), msg)

        # Check if change can see in History change
        history_device = HistoryChange.objects.filter(
            device=self.device,
            old_value='Very important device',
            new_value='Hello Ralph',
        )
        self.assertEqual(history_device.count(), 1)
        self.assertEqual(
            history_device[0].comment,
            'Everything has changed'
        )

    def test_many_devices_edit(self):
        url = '/ui/search/bulkedit/'
        remarks = 'change remarks in 2 devices'

        post_data = {
            'select': [self.device.id, self.device2.id],
            'edit': ['remarks'],
            'remarks': remarks,
            'save_comment': 'change remarks',
            'save': '',  # save form
        }
        self.client.post(url, post_data)

        device, device2 = Device.objects.filter(remarks=remarks)
        self.assertEqual = (device.remarks, remarks)
        self.assertEqual = (device.remarks, device2.remarks)

    def test_send_form_without_marking_edited_fields(self):
        url = '/ui/search/bulkedit/'
        data_post = {
            'select': self.device.id,
            'remarks': 'Here are some remarks without confirmation.',
            'save': '',
        }
        response = self.client.post(url, data_post)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ERROR_MSG['no_mark_fields'] in response.content)

    def test_send_form_with_empty_save_comment_field(self):
        url = '/ui/search/bulkedit/?'
        post_data = {
            'select': [self.device.id],
            'edit': ['remarks'],
            'remarks': 'Hello World!',
            'save_comment': '',
            'save': '',  # save form
        }
        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ERROR_MSG['empty_save_comment'] in response.content)
        self.assertFormError(
            response,
            'form',
            'save_comment',
            ERROR_MSG['empty_save_comment_field']
        )
