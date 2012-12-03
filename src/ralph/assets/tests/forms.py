# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase
from ralph.assets.models_assets import (
    Asset, AssetModel, AssetManufacturer, AssetSource, AssetStatus, AssetType,
    DeviceInfo, LicenseTypes, OfficeInfo, Warehouse
)
from ralph.ui.tests.helper import login_as_su


def create_menufacturer(name):
    menufacturer = AssetManufacturer(name=name)
    menufacturer.save()
    return menufacturer


def create_model(menufacturer, name):
    model = AssetModel(
        manufacturer=menufacturer,
        name=name,
    )
    model.save()
    return model


def create_warehouse(name):
    warehouse = Warehouse(name=name)
    warehouse.save()
    return warehouse


def create_device(size, warehouse):
    device = DeviceInfo(
        size=size,
        warehouse=warehouse,
    )
    device.save()
    return device


def create_asset(**kwargs):
    asset = Asset(**kwargs)
    asset.save()
    return asset


class TestForms(TestCase):
    def setUp(self):
        self.client = login_as_su()
        # Build asset
        asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=create_model(create_menufacturer('Menufac'), 'AsModel'),
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
        # Prepare Asset 2
        self.asset_model2 = create_model(
            create_menufacturer('Menufac2'), 'AsModel2'
        )
        self.device_info2 = create_device(
            1, create_warehouse(name='Warehouse2')
        )
        # Prepare Asset 3
        self.asset_model3 = create_model(
            create_menufacturer('Menufac3'), 'AsModel3'
        )

    def test_models(self):
        db_menufacturer = AssetManufacturer.objects.get(name='Menufac')
        self.assertEquals(db_menufacturer.name, 'Menufac')
        db_model = AssetModel.objects.get(name='AsModel')
        self.assertEquals(db_model.name, 'AsModel')
        db_warehouse = Warehouse.objects.get(name='Warehouse1')
        self.assertEquals(db_warehouse.name, 'Warehouse1')
        db_asset1 = Asset.objects.get(barcode='bc-1234')
        self.assertEquals(db_asset1.sn, 'sn-123')

    def test_view(self):
        url = '/assets/dc/search'
        view = self.client.get(url, follow=True)
        self.assertEqual(view.status_code, 200)
        data = view.context_data['page'].object_list[0]
        self.assertEqual(data.type, AssetType.data_center)
        self.assertEqual(data.sn, 'sn-123')
        self.assertEqual(data.barcode, 'bc-1234')
        self.assertEqual(unicode(data.model), 'AsModel')
        self.assertEqual(data.invoice_no, 'Invoice No 1')
        self.assertEqual(data.order_no, 'Order No 1')
        date = datetime.date(2001, 1, 1)
        self.assertEqual(data.buy_date, date)
        self.assertEqual(data.status, AssetStatus.new)
        self.assertEqual(unicode(data.device_info.warehouse), 'Warehouse1')

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
        response = self.client.post(url, post_data, follow=True)
        self.assertRedirects(
            response, '/assets/dc/search',
            status_code=302,
            target_status_code=200,
        )
        # GET
        view = self.client.get('/assets/dc/search')
        data = view.context_data['page'].object_list[1]
        self.assertEqual(data.type, AssetType.data_center)
        self.assertEqual(data.sn, 'sn-321')
        self.assertEqual(data.barcode, 'bc-4321')
        self.assertEqual(unicode(data.model), 'AsModel2')
        self.assertEqual(data.invoice_no, 'Invoice No 2')
        self.assertEqual(data.order_no, 'Order No 2')
        date = datetime.date(2001, 1, 2)
        self.assertEqual(data.buy_date, date)
        self.assertEqual(data.status, AssetStatus.new)
        self.assertEqual(unicode(data.device_info.warehouse), 'Warehouse2')

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
        post = self.client.post(url, post_data, follow=True)
        self.assertRedirects(
            post,
            '/assets/dc/search',
            status_code=302,
            target_status_code=200,
        )
        # Tests after POST
        new_view = self.client.get('/assets/dc/edit/device/1/')
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


class TestBulkEdit(TestCase):
    def setUp(self):
        self.client = login_as_su()
        # Build asset
        self.asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=create_model(create_menufacturer('Menufac1'), 'AsModel1'),
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
        # Build asset 2
        self.asset2 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse2')),
            type=AssetType.data_center,
            model=create_model(create_menufacturer('Menufac2'), 'AsModel2'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 2',
            order_no='Order No 2',
            buy_date=datetime.datetime(2002, 01, 01),
            support_period=22,
            support_type='Support d2d',
            provider='Provider 2',
            status=AssetStatus.new,
            sn='sn-1232',
            barcode='bc-12342'
        )

    def test_bulkedit_form(self):
        # Before send POST
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.asset.id, self.asset2.id)
        view = self.client.get(url)
        self.assertEqual(view.status_code, 200)
        model0 = create_model(create_menufacturer('Menufac1a'), 'AsModel1a')
        model1 = create_model(create_menufacturer('Menufac2a'), 'AsModel2a')
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,
            'form-0-model': model0.id,
            'form-0-invoice_no': 'Invoice No 1a',
            'form-0-order_no': 'Order No 1a',
            'form-0-buy_date': '2012-02-02',
            'form-0-sn': 'sn-321-2012a',
            'form-0-barcode': 'bc-4321-2012a',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider 1a',
            'form-0-status': AssetStatus.in_progress.id,
            'form-0-source': AssetSource.shipment.id,
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,
            'form-1-model': model1.id,
            'form-1-invoice_no': 'Invoice No 2a',
            'form-1-order_no': 'Order No 2a',
            'form-1-buy_date': '2011-02-03',
            'form-1-sn': 'sn-321-2012b',
            'form-1-barcode': 'bc-4321-2012b',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider 2a',
            'form-1-status': AssetStatus.waiting_for_release.id,
            'form-1-source': AssetSource.shipment.id,
        }
        post = self.client.post(url, post_data, follow=True)
        self.assertRedirects(
            post, url, status_code=302, target_status_code=200,
        )
        new_view = self.client.get(url)
        fields = new_view.context['formset'].queryset
        # model
        self.assertEqual(fields[0].model.id, model0.id)
        self.assertEqual(fields[1].model.id, model1.id)
        # invoice_no
        self.assertEqual(fields[0].invoice_no, 'Invoice No 1a')
        self.assertEqual(fields[1].invoice_no, 'Invoice No 2a')
        # order_no
        self.assertEqual(fields[0].order_no, 'Order No 1a')
        self.assertEqual(fields[1].order_no, 'Order No 2a')
        # Buy date
        self.assertEqual(unicode(fields[0].buy_date), '2012-02-02')
        self.assertEqual(unicode(fields[1].buy_date), '2011-02-03')
        # Support period in months
        self.assertEqual(fields[0].support_period, 24)
        self.assertEqual(fields[1].support_period, 48)
        # Support type
        self.assertEqual(fields[0].support_type, 'standard1')
        self.assertEqual(fields[1].support_type, 'standard2')
        # Provider
        self.assertEqual(fields[0].provider, 'Provider 1a')
        self.assertEqual(fields[1].provider, 'Provider 2a')
        # Status
        self.assertEqual(fields[0].status, AssetStatus.in_progress.id)
        self.assertEqual(fields[1].status, AssetStatus.waiting_for_release.id)
        # SN
        self.assertEqual(fields[0].sn, 'sn-321-2012a')
        self.assertEqual(fields[1].sn, 'sn-321-2012b')
        # Barcode
        self.assertEqual(fields[0].barcode, 'bc-4321-2012a')
        self.assertEqual(fields[1].barcode, 'bc-4321-2012b')


class TestSearchForm(TestCase):
    def setUp(self):
        self.client = login_as_su()
        model = create_model(create_menufacturer('Menufac1'), 'AsModel1')
        self.asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=model,
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            buy_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-12332452345',
            barcode='bc-123421141'
        )
        self.asset1 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse2')),
            type=AssetType.data_center,
            model=create_model(create_menufacturer('Menufac2'), 'AsModel2'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 3',
            buy_date=datetime.datetime(2003, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 2',
            status=AssetStatus.in_service,
            sn='sn-123123123',
            barcode='bc-1234123123'
        )
        self.asset2 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse3')),
            type=AssetType.data_center,
            model=model,
            source=AssetSource.shipment,
            invoice_no='Invoice No 3',
            order_no='Order No 3',
            buy_date=datetime.datetime(2002, 01, 01),
            support_period=12,
            support_type='standard',
            provider='Provider 3',
            status=AssetStatus.used,
            sn='sn-12323542345',
            barcode='bc-12341234124'
        )

    def test_model(self):
        url = '/assets/dc/search?model=%s' % self.asset.id
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)
        output = ('<Asset: AsModel2 - sn-123123123 - bc-1234123123>')
        self.assertNotEqual(unicode(res[0]), output)
        # Empty ?model=
        url = '/assets/dc/search?model='
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 3)
        url = '/assets/dc/search?model=99999'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 404)

    def test_invoice(self):
        url = '/assets/dc/search?invoice_no=%s' % 'Invoice No 1'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)
        output = ('<Asset: AsModel3 - sn-12323542345 - bc-12341234124>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_order(self):
        url = '/assets/dc/search?order_no=%s' % 'Order No 3'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)
        output = ('<Asset: AsModel1 - sn-12332452345 - bc-123421141>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_provider(self):
        url = '/assets/dc/search?provider=%s' % 'Provider 3'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        output = ('<Asset: AsModel1 - sn-12332452345 - bc-123421141>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_status(self):
        url = '/assets/dc/search?status=%s' % AssetStatus.used.id
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        output = ('AsModel1 - sn-12323542345 - bc-12341234124')
        self.assertEqual(unicode(res[0]), output)

    def test_sn(self):
        url = '/assets/dc/search?sn=%s' % 'sn-123123123'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        output = ('AsModel2 - sn-123123123 - bc-1234123123')
        self.assertEqual(unicode(res[0]), output)

    def test_date_range(self):
        # beggining date should be equal than end date
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        output = ('AsModel1 - sn-12332452345 - bc-123421141')
        self.assertEqual(unicode(res[0]), output)
        # beggining date should be lower than end date
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)
        output = ('AsModel2 - sn-123123123 - bc-1234123123')
        self.assertNotEqual(unicode(res[0]), output)
        # beggining date cant be lower than end date
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 0)
        # beggining date is None, end date is desirable
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '', '2001-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        # beggining date is None, end date is lower then youngest object
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '', '1999-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 0)
        # beggining date is correct, end date is None
        url = '/assets/dc/search?buy_date_from=%s&buy_date_to=%s' % (
            '1999-01-01', '')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 3)


class TestTrolling(TestCase):
    def setUp(self):
        self.client = login_as_su()

    def test_empty_form(self):
        url = '/assets/back_office/add/device/'
        post_data = {}
        post = self.client.post(url, post_data)
        self.assertEqual(post.status_code, 200)
        self.assertFormError(
            post, 'asset_form', 'model', 'This field is required.'
        )
        self.assertFormError(
            post, 'asset_form', 'support_period', 'This field is required.'
        )
        self.assertFormError(
            post, 'asset_form', 'support_type', 'This field is required.'
        )
        self.assertFormError(
            post, 'device_info_form', 'warehouse', 'This field is required.'
        )
        self.assertFormError(
            post, 'asset_form', 'sn', 'This field is required.'
        )

    def test_invalid_fueld_value(self):
        # instead of integers we send strings, error should be thrown
        url = '/assets/back_office/add/device/'
        post_data = {
            'support_period': 'string',
            'size': 'string',
            'buy_date': 'string'
        }
        post = self.client.post(url, post_data)
        self.assertEqual(post.status_code, 200)
        self.assertFormError(
            post, 'asset_form', 'support_period', 'Enter a whole number.'
        )
        self.assertFormError(
            post, 'device_info_form', 'size', 'Enter a whole number.'
        )
        self.assertFormError(
            post, 'asset_form', 'buy_date', 'Enter a valid date.'
        )
