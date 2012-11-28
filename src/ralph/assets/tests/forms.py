# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

import datetime

from ralph.assets.models_assets import (
    Asset, AssetModel, AssetManufacturer, AssetSource, AssetStatus, AssetType,
    DeviceInfo, Warehouse
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
        data = view.context['data']
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

    def test_form(self):
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
        # if not - find errors
        #self.assertEqual(post.context_data['asset_form']._errors, {})
        #self.assertEqual(post.context_data['device_info_form']._errors, {})
        # GET
        view = self.client.get('/assets/dc/search')
        self.assertEqual(view.status_code, 200)
        data = view.context['data']
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
