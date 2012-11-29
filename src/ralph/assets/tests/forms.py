# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

import datetime

from ralph.assets.models_assets import (
    Asset, AssetModel, AssetManufacturer, AssetSource, AssetStatus, AssetType,
    DeviceInfo, LicenseTypes, OfficeInfo, Warehouse
)
from ralph.ui.tests.helper import login_as_su


class TestFormsAdd(TestCase):
    def setUp(self):
        self.client = login_as_su()
        # Add menufacture
        asset_menufacture = AssetManufacturer(
            name='Menufac'
        )
        asset_menufacture.save()
        # Add Asset Model
        asset_model = AssetModel(
            manufacturer=asset_menufacture,
            name='AsModel',
        )
        asset_model.save()
        # Add Warehouse
        warehouse = Warehouse(name='Warehouse1')
        warehouse.save()
        # Add device_info
        device_info = DeviceInfo(
            size=1,
            warehouse=warehouse,
        )
        device_info.save()
        self.device_info = device_info
        # Add Asset Model
        asset_model2 = AssetModel(
            manufacturer=asset_menufacture,
            name='AsModel2',
        )
        asset_model2.save()
        self.asset_model2 = asset_model2
        # Add werehouse2
        warehouse2 = Warehouse(name='Warehouse2')
        warehouse2.save()
        # Add device_info
        device_info2 = DeviceInfo(
            size=1,
            warehouse=warehouse2,
        )
        device_info2.save()
        self.device_info2 = device_info2

        # Add Asset Model
        asset_model3 = AssetModel(
            manufacturer=asset_menufacture,
            name='AsModel3',
        )
        asset_model3.save()
        self.asset_model3 = asset_model3
        # Add device
        asset1 = Asset(
            device_info=device_info,
            type=AssetType.data_center,
            model=asset_model,
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            buy_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-123',
            barcode='bc-1234'
        )
        asset1.save()

    def test_models(self):
        db_menufacture = AssetManufacturer.objects.get(name='Menufac')
        self.assertEquals(db_menufacture.name, 'Menufac')
        db_model = AssetModel.objects.get(name='AsModel')
        self.assertEquals(db_model.name, 'AsModel')
        db_warehouse = Warehouse.objects.get(name='Warehouse1')
        self.assertEquals(db_warehouse.name, 'Warehouse1')
        db_asset1 = Asset.objects.get(barcode='bc-1234')
        self.assertEquals(db_asset1.sn, 'sn-123')

    def test_view(self):
        url ='/assets/dc/search'
        view = self.client.get(url, follow=True)
        self.assertEqual(view.status_code, 200)
        data = view.context_data['page'].object_list
        self.assertEqual(data[0].type, AssetType.data_center)
        self.assertEqual(data[0].sn, 'sn-123')
        self.assertEqual(data[0].barcode, 'bc-1234')
        self.assertEqual(unicode(data[0].model), 'AsModel')
        self.assertEqual(data[0].invoice_no, 'Invoice No 1')
        self.assertEqual(data[0].order_no, 'Order No 1')
        date = datetime.date(2001, 01, 01)
        self.assertEqual(data[0].buy_date, date)
        self.assertEqual(data[0].status, AssetStatus.new)
        self.assertEqual(unicode(data[0].device_info.warehouse), 'Warehouse1')

    def test_add_form(self):
        # POST
        url = '/assets/dc/add/device/'
        post_data = {
            'type': AssetType.data_center,
            'model': self.asset_model2.id,
            'source': AssetSource.shipment,
            'invoice_no': 'Invoice No 2',
            'order_no': 'Order No 2',
            'buy_date': '2001-01-02',
            'support_period': 12,
            'support_type': 'Support d2d',
            'support_void_reporting': 'on',
            'provider': 'Provider 2',
            'status': AssetStatus.new,
            'size': 1,
            'sn': 'sn-321',
            'barcode': 'bc-4321',
            'warehouse': self.device_info2.warehouse_id,
        }
        post = self.client.post(url, post_data)
        self.assertEquals(post.status_code, 302)
        # GET
        view = self.client.get('/assets/dc/search')
        self.assertEqual(view.status_code, 200)
        data = view.context_data['page'].object_list
        self.assertEqual(data[1].type, AssetType.data_center)
        self.assertEqual(data[1].sn, 'sn-321')
        self.assertEqual(data[1].barcode, 'bc-4321')
        self.assertEqual(unicode(data[1].model), 'AsModel2')
        self.assertEqual(data[1].invoice_no, 'Invoice No 2')
        self.assertEqual(data[1].order_no, 'Order No 2')
        date = datetime.date(2001, 01, 02)
        self.assertEqual(data[1].buy_date, date)
        self.assertEqual(data[1].status, AssetStatus.new)
        self.assertEqual(unicode(data[1].device_info.warehouse), 'Warehouse2')

    def test_edit_form(self):
        # test before POST
        view = self.client.get('/assets/dc/edit/device/1/')
        self.assertEqual(view.status_code, 200)
        old_fields = view.context['asset_form'].initial
        old_device_info = view.context['device_info_form'].initial
        old_office_info = view.context['office_info_form'].initial
        old_office = OfficeInfo.objects.filter(
            license_key='0000-0000-0000-0000'
        ).count()
        self.assertEqual(old_office, 0)
        # Send POST
        url = '/assets/dc/edit/device/1/'
        post_data = {
            'type': AssetType.data_center,
            'model': self.asset_model3.id,
            'invoice_no': 'Invoice No 3',
            'order_no': 'Order No 3',
            'buy_date': '2001-02-02',
            'support_period': 24,
            'support_type': 'standard',
            'support_void_reporting': 'on',
            'provider': 'Provider 3',
            'status': AssetStatus.in_progress,
            'size': 2,
            'sn': 'sn-321-2012',
            'barcode': 'bc-4321-2012',
            'warehouse': self.device_info2.warehouse_id,
            'remarks': 'any remarks',
            'size': 2,
            'license_key': '0000-0000-0000-0000',
            'version': '1.0',
            'unit_price': 2.00,
            'license_type': LicenseTypes.oem,
            'buy_date': '2001-02-02',
            'date_of_last_inventory': '2003-02-02',
            'last_logged_user': 'James Bond',
            }
        post = self.client.post(url, post_data)
        self.assertEquals(post.status_code, 302)
        # Tests after POST
        new_view = self.client.get('/assets/dc/edit/device/1/')
        self.assertEqual(new_view.status_code, 200)
        new_fields = new_view.context['asset_form'].initial
        new_device_info = new_view.context['device_info_form'].initial
        new_office_info = new_view.context['office_info_form'].initial
        # type
        self.assertEqual(old_fields['type'], new_fields['type'])
        # model
        self.assertNotEqual(old_fields['model'], new_fields['model'])
        self.assertEqual(new_fields['model'], self.asset_model3.id)
        # invoice_no
        self.assertNotEqual(old_fields['invoice_no'], new_fields['invoice_no'])
        self.assertEqual(new_fields['invoice_no'], 'Invoice No 3')
        # order_no
        self.assertNotEqual(old_fields['order_no'], new_fields['order_no'])
        self.assertEqual(new_fields['order_no'], 'Order No 3')
        # Buy date
        self.assertNotEqual(old_fields['buy_date'], new_fields['buy_date'])
        self.assertEqual(unicode(new_fields['buy_date']), '2001-02-02')
        # Support period in months
        self.assertNotEqual(
            old_fields['support_period'], new_fields['support_period']
        )
        self.assertEqual(new_fields['support_period'], 24)
        # Support type
        self.assertNotEqual(
            old_fields['support_type'], new_fields['support_type']
        )
        self.assertEqual(new_fields['support_type'], 'standard')
        # Provider
        self.assertNotEqual(old_fields['provider'], new_fields['provider'])
        self.assertEqual(new_fields['provider'], 'Provider 3')
        # Status
        self.assertNotEqual(old_fields['status'], new_fields['status'])
        self.assertEqual(new_fields['status'], AssetStatus.in_progress)
        # SN
        self.assertNotEqual(old_fields['sn'], new_fields['sn'])
        self.assertEqual(new_fields['sn'], 'sn-321-2012')
        # Barcode
        self.assertNotEqual(old_fields['barcode'], new_fields['barcode'])
        self.assertEqual(new_fields['barcode'], 'bc-4321-2012')
        # Additional remarks
        self.assertEqual(old_fields['remarks'], None)
        self.assertEqual(new_fields['remarks'], 'any remarks')
        # Size in units
        self.assertNotEqual(old_device_info['size'], new_device_info['size'])
        self.assertEqual(new_device_info['size'], 2)
        # License key
        office = OfficeInfo.objects.filter(
            license_key='0000-0000-0000-0000'
        ).count()
        self.assertEqual(office, 1)
        self.assertEqual(old_office_info, {})
        self.assertEqual(new_office_info['license_key'], '0000-0000-0000-0000')
        # Version
        self.assertEqual(new_office_info['version'], '1.0')
        # Unit price
        self.assertEqual(new_office_info['unit_price'], 2.00)
        # License type
        self.assertEqual(new_office_info['license_type'], LicenseTypes.oem)
        # Date of last inventory
        self.assertEqual(
            unicode(new_office_info['date_of_last_inventory']), '2003-02-02'
        )
        # Last logged user
        self.assertEqual(new_office_info['last_logged_user'], 'James Bond')
