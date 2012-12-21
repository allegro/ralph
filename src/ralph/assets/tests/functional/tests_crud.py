# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.assets.models_assets import *
from ralph.assets.tests.util import (
    create_model, create_warehouse, create_asset
)
from ralph.ui.tests.helper import login_as_su


class TestAdding(TestCase):
    """Test adding single asset"""

    def setUp(self):
        self.client = login_as_su()
        self.model = create_model()
        self.model2 = create_model('Model2')
        self.warehouse = create_warehouse()
        self.warehouse2 = create_warehouse('Warehouse2')
        self.asset = create_asset(
            sn='1111-1111-1111-1111',
        )

    def test_send_data_via_add_form(self):
        url = '/assets/dc/add/device/'
        data_in_add_form = dict(
            type=AssetType.data_center.id,  # 1
            model=self.model.id,  # u'Model1'
            source=AssetSource.shipment.id,  # 1
            invoice_no='Invoice No1',
            order_no='Order no1',
            invoice_date='2001-01-01',
            support_period=48,
            support_type='standard',
            support_void_reporting=True,
            provider='Provider2',
            status=AssetStatus.new.id,  # 1
            size=1,
            price=11,
            request_date='2001-01-02',
            delivery_date='2001-01-03',
            production_use_date='2001-01-04',
            sn='2222-2222-2222-2222',
            barcode='bc-1111-1111-1111',
            warehouse=self.warehouse.id,  # 1
        )
        send_post = self.client.post(url, data_in_add_form)

        # If everything is ok, redirect us to /assets/dc/search
        self.assertRedirects(
            send_post,
            '/assets/dc/edit/device/2/',
            status_code=302,
            target_status_code=200,
        )

        view = self.client.get('/assets/dc/search')
        row_from_table = view.context_data['bob_page'].object_list[1]

        # Overwriting variables to use the object to test the output.
        data_in_add_form.update(
            model='Manufacturer1 Model1',
            warehouse='Warehouse',
        )
        # Test comparison input data and output data
        for field in data_in_add_form:
            input = data_in_add_form[field]
            if field == 'size':
                output = row_from_table.device_info.size
            else:
                output = getattr(row_from_table, field)
            msg = 'Field: %s Input: %s Output: %s' % (field, input, output)
            self.assertEqual(unicode(input), unicode(output), msg)

    def test_send_data_via_edit_form(self):
        # Fetch data
        view = self.client.get('/assets/dc/edit/device/1/')
        self.assertEqual(view.status_code, 200)
        old_fields = view.context['asset_form'].initial
        if view.context['device_info_form']:
            old_device_info = view.context['device_info_form'].initial
        url = '/assets/dc/edit/device/1/'
        data_in_edit_form = dict(
            type=AssetType.data_center.id,  # 1
            model=self.model2.id,  # u'Model1'
            source=AssetSource.shipment.id,  # 1
            invoice_no='Invoice No2',
            order_no='Order No2',
            support_period=12,
            support_type='d2d',
            support_void_reporting=True,
            provider='Provider2',
            status=AssetStatus.in_progress.id,  # 1
            size=2,
            invoice_date='2001-02-02',
            request_date='2001-01-02',
            delivery_date='2001-01-03',
            production_use_date='2001-01-04',
            provider_order_date='2001-01-05',
            sn='3333-3333-3333-333',
            barcode='bc-3333-3333-333',
            warehouse=self.warehouse.id,  # 1
            license_key='0000-0000-0000-0000',
            version='1.0',
            price=2.00,
            license_type=LicenseType.oem,
            date_of_last_inventory='2003-02-02',
            last_logged_user='James Bond',
            remarks='any remarks',
        )
        post = self.client.post(url, data_in_edit_form, follow=True)

        # if everything is ok, server return response code = 302, and
        # redirect us to /assets/dc/search with target status code 200
        self.assertRedirects(
            post,
            '/assets/dc/edit/device/1/',
            status_code=302,
            target_status_code=200,
        )
        # Fetch added data
        new_view = self.client.get('/assets/dc/edit/device/1/')
        new_fields = new_view.context['asset_form'].initial
        new_device_info = new_view.context['device_info_form'].initial
        if new_view.context['office_info_form']:
            new_office_info = new_view.context['office_info_form'].initial

        correct_data = [
            dict(
                model=self.model2.id,
                invoice_no='Invoice No2',
                order_no='Order No2',
                invoice_date='2001-02-02',
                request_date='2001-01-02',
                delivery_date='2001-01-03',
                production_use_date='2001-01-04',
                provider_order_date='2001-01-05',
                support_period=12,
                support_type='d2d',
                provider='Provider2',
                status=AssetStatus.in_progress.id,
                remarks='any remarks',
            )
        ]
        for data in correct_data:
            for key in data.keys():
                self.assertNotEqual(
                    unicode(old_fields[key]), unicode(new_fields[key])
                )
                self.assertEqual(
                    unicode(new_fields[key]), unicode(data[key])
                )

        self.assertNotEqual(old_device_info['size'], new_device_info['size'])
        self.assertEqual(new_device_info['size'], 2)
        office = OfficeInfo.objects.filter(
            license_key='0000-0000-0000-0000'
        ).count()
        if new_view.context['office_info_form']:
            self.assertEqual(office, 1)
            self.assertEqual(old_office_info, {})
            self.assertEqual(
                new_office_info['license_key'], '0000-0000-0000-0000'
            )

        correct_data_office = [
            dict(
                version='1.0',
                license_type=LicenseType.oem.id,
                date_of_last_inventory='2003-02-02',
                last_logged_user='James Bond',
            )
        ]
        if new_view.context['office_info_form']:
            for office in correct_data_office:
                for key in office.keys():
                    self.assertEqual(
                        unicode(new_office_info[key]), unicode(office[key])
                    )

    def test_delete_asset(self):
        """todo"""
        pass
