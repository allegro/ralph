# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import datetime

from django.test import TestCase
from business.models import Venture, VentureRole
from discovery.models_device import Device, DeviceType, DeprecationKind, MarginKind
from discovery.models_history import HistoryChange

from ralph.ui.tests.global_utils import login_as_su


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

ERROR_MSG = {
    'no_mark_fields': 'You have to mark which fields you changed',
    'empty_save_comment': 'Correct the errors.',
    'empty_save_comment_field': 'You must describe your change',
}

class TestBulkedit(TestCase):
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

        self.deprecation_kind=DeprecationKind(months=24, remarks='Default')
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

    def test_single_device_edit(self):
        url = '/ui/search/bulkedit/'

        select_fields = (
            'venture', 'venture_role', 'margin_kind', 'deprecation_kind',
        )
        date_fields = (
            'purchase_date', 'warranty_expiration_date',
            'support_expiration_date', 'support_kind',
        )
        text_fields = (
            'barcode', 'position', 'chassis_position', 'remarks', 'price',
            'sn', 'verified'
        )
        device_fields = []

        for list in [select_fields, date_fields, text_fields]:
            device_fields.extend(list)

        post_data = {
             'select': [self.device.id],  # 1
             'edit': device_fields,
             'venture': self.venture.id,  # 1
             'venture_role': self.role.id,  # 1
             'verified': True,
             'barcode': 'bc-2222-2222-2222-2222',
             'position': '9',
             'chassis_position': 10,
             'remarks': 'Hello Ralph',
             'margin_kind': self.margin.id,  # 1
             'deprecation_kind': self.deprecation_kind.id,  # 1
             'price': 100,
             'sn': '2222-2222-2222-2222',
             'purchase_date': '2001-01-01',
             'warranty_expiration_date': '2001-01-02',
             'support_expiration_date': '2001-01-03',
             'support_kind': '2001-01-04',
             'save_comment': 'Everything has changed',
             'save': '',  # save form
         }
        response = self.client.post(url, post_data)

        # Check if data from form is the same that data in database
        device = Device.objects.get(id=self.device.id)

        for field in device_fields:
            db_data = getattr(device, field)
            form_data = post_data[field]
            msg = 'FIELD: %s, DB: %s FORM: %s' % (field, db_data, form_data)

            if field in select_fields:
                self.assertEqual(db_data.id, form_data, msg)
            elif field in date_fields:
                self.assertEqual(unicode(db_data)[0:10], form_data, msg)
            else:
                self.assertEqual(db_data, form_data, msg)

        # Check if change can see in History change
       #TODO


    def test_many_devices_edit(self):
        pass

    def test_send_form_without_selected_edit_fields(self):
        url = '/ui/search/bulkedit/'
        data_post = {
            'select': self.device.id,
            'bulk': '',  # show form
        }
        response = self.client.post(url, data_post)

        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {'select': self.device.id})
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
        response = self.client.post(url, post_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ERROR_MSG['empty_save_comment'] in response.content)
        self.assertFormError(
            response, 'form', 'save_comment',
            ERROR_MSG['empty_save_comment_field']
        )

    def test_calculation_depreciation_date(self):
        device = Device.objects.get(id=self.device.id)
        self.assertEqual(device.purchase_date, None)
        self.assertEqual(device.deprecation_kind, None)

        url = '/ui/search/bulkedit/?'
        post_data = {
            'select': [self.device.id],  # 1
            'edit': ['purchase_date', 'deprecation_kind'],
            'purchase_date': '2001-01-01',
            'deprecation_kind': self.deprecation_kind.id,  # 1
            'save_comment': 'Updated: purchase date and  deprecation kind',
            'save': '',  # save form
        }
        response = self.client.post(url, post_data, follow=True)

        updated_device = Device.objects.get(id=self.device.id)
        self.assertEqual(
            unicode(updated_device.purchase_date),
            '2001-01-01 00:00:00'
        )
        self.assertEqual(updated_device.deprecation_kind.months, 24)
        self.assertEqual(
            unicode(updated_device.deprecation_date),
            '2003-01-01 00:00:00'
        )

        # Check if purchase date,change deprecation date
        post_data = {
            'select': [self.device.id],  # 1
            'edit': ['purchase_date'],
            'purchase_date': '2002-01-01',
            'save_comment': 'Updated: purchase date',
            'save': '',  # save form
        }
        response = self.client.post(url, post_data, follow=True)

        updated_device2 = Device.objects.get(id=self.device.id)
        self.assertEqual(
            unicode(updated_device2.deprecation_date),
            '2004-01-01 00:00:00'
        )
