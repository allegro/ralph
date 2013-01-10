# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

import datetime

from ralph.assets.tests.util import create_asset, create_model, create_category
from ralph.assets.models_assets import AssetStatus
from ralph.ui.tests.global_utils import login_as_su


class TestSearchForm(TestCase):
    """Scenario:
    1. Tests all fields
    2. Insert incorrect data
    """
    def setUp(self):
        self.client = login_as_su()
        self.category = create_category()
        self.first_asset = create_asset(
            invoice_no='Invoice No1',
            order_no='Order No2',
            invoice_date=datetime.date(2001, 1, 1),
            support_type='Support d2d',
            provider='Provider1',
            sn='1234-1234-1234-1234',
            barcode='bc1',
            category=self.category,
        )

        self.second_asset = create_asset(
            invoice_no='Invoice No2',
            order_no='Order No1',
            invoice_date=datetime.date(2001, 1, 1),
            support_type='Support d2d',
            provider='Provider2',
            sn='1235-1235-1235-1235',
            barcode='bc2',
            category=self.category,
        )

        asset_model = create_model(name='Model2')
        asset_status = AssetStatus.used.id
        self.third_asset = create_asset(
            model=asset_model,
            invoice_no='Invoice No1',
            order_no='Order No1',
            invoice_date=datetime.date(2001, 1, 1),
            support_type='Support d2d',
            provider='Provider1',
            sn='1236-1236-1236-1236',
            barcode='bc3',
            status=asset_status,
            category=self.category,
        )

    def test_model_field(self):
        self.assertEqual(self.first_asset.model.name, 'Model1')

        url = '/assets/dc/search?model=%s' % self.first_asset.model.name
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        # Test if search form find correct data
        self.assertItemsEqual(
            [asset.model.name for asset in rows_from_table],
            ['Model1', 'Model1']
        )
        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

        # What do Ralph when we don't insert model name? (return all asset)
        content = self.client.get('/assets/dc/search?model=')
        self.assertEqual(content.status_code, 200)
        empty_model_rows = content.context_data['bob_page'].object_list
        self.assertEqual(len(empty_model_rows), 3)

        # or we insert wrong model name (outside range)?
        content = self.client.get('/assets/dc/search?model=Ralph0')
        self.assertEqual(content.status_code, 200)
        outside_range_rows = content.context_data['bob_page'].object_list
        self.assertEqual(len(outside_range_rows), 0)

    def test_invoice_no_field(self):
        self.assertEqual(self.third_asset.invoice_no, 'Invoice No1')

        url = '/assets/dc/search?invoice_no=%s' % self.third_asset.invoice_no
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        # Test if search form find correct data
        self.assertItemsEqual(
            [asset.invoice_no for asset in rows_from_table],
            ['Invoice No1', 'Invoice No1']
        )
        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1236-1236-1236-1236']
        )

    def test_order_no_field(self):
        self.assertEqual(self.third_asset.order_no, 'Order No1')
        url = '/assets/dc/search?order_no=%s' % self.third_asset.order_no
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        # Test if search form find correct data
        self.assertItemsEqual(
            [asset.order_no for asset in rows_from_table],
            ['Order No1', 'Order No1']
        )
        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1235-1235-1235-1235', '1236-1236-1236-1236']
        )

    def test_provider_field(self):
        self.assertEqual(self.second_asset.provider, 'Provider2')
        url = '/assets/dc/search?provider=%s' % self.second_asset.provider
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)

        # Test if search form find correct data
        self.assertEqual(rows_from_table[0].provider, 'Provider2')
        self.assertEqual(rows_from_table[0].sn, '1235-1235-1235-1235')

    def test_status_field(self):
        self.assertEqual(
            AssetStatus.name_from_id(self.third_asset.status), 'used'
        )
        url = '/assets/dc/search?status=%s' % AssetStatus.used.id
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)

        # Test if search form find correct data
        self.assertItemsEqual(
            [AssetStatus.name_from_id(asset.status) for asset in rows_from_table],
            ['used']
        )
        self.assertEqual(rows_from_table[0].sn, '1236-1236-1236-1236')

    def test_sn_field(self):
        self.assertEqual(self.first_asset.sn, '1234-1234-1234-1234')
        url = '/assets/dc/search?sn=%s' % self.first_asset.sn
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)

        # Test if search form find correct data
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_type_filed(self):
        device = '/assets/dc/search?part_info=device'
        part = '/assets/dc/search?part_info=part'

        # Here we tests if in page see only devices.
        device_content = self.client.get(device)
        self.assertEqual(device_content.status_code, 200)
        dev_data = device_content.context_data['bob_page'].object_list

        for dev in dev_data:
            self.assertEqual(dev.part_info, None)

        # Here we tests if in page see only a parts..
        part_content = self.client.get(part)
        self.assertEqual(part_content.status_code, 200)
        part_data = part_content.context_data['bob_page'].object_list

        for part in part_data:
            self.assertNotEqual(part.part_info, None)

class TestSearchInvoiceDateFields(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.category = create_category()
        self.first_asset = create_asset(
            invoice_date=datetime.date(2001, 1, 1),
            sn='1234-1234-1234-1234',
            category=self.category,
        )

        self.second_asset = create_asset(
            invoice_date=datetime.date(2002, 1, 1),
            sn='1235-1235-1235-1235',
            category=self.category,
        )

        self.third_asset = create_asset(
            invoice_date=datetime.date(2003, 1, 1),
            sn='1236-1236-1236-1236',
            category=self.category,
        )

    def test_start_date_is_equal_end_date(self):
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_start_date_is_less_then_end_date(self):
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 0)

    def test_find_more_assets_lte_gte(self):
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

    def test_start_date_is_empty(self):
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_end_date_is_empty(self):
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '1999-01-01', '')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 3)

class TestSearchProviderDateFields(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.base_url = '/assets/dc/search'

        self.first_asset = create_asset(
            provider_order_date=datetime.date(2001, 1, 1),
            sn='1234-1234-1234-1234',
        )

        self.second_asset = create_asset(
            provider_order_date=datetime.date(2002, 1, 1),
            sn='1235-1235-1235-1235',
        )

        self.third_asset = create_asset(
            provider_order_date=datetime.date(2003, 1, 1),
            sn='1236-1236-1236-1236',
        )

    def test_start_date_is_equal_end_date(self):
        url = '?provider_order_date_from=%s&provider_order_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_start_date_is_less_then_end_date(self):
        url = '?provider_order_date_from=%s&provider_order_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 0)

    def test_find_more_assets_lte_gte(self):
        url = '?provider_order_date_from=%s&provider_order_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

    def test_start_date_is_empty(self):
        url = '?provider_order_date_from=%s&provider_order_date_to=%s' % (
            '', '2001-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_end_date_is_empty(self):
        url = '?provider_order_date_from=%s&provider_order_date_to=%s' % (
            '1999-01-01', '')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 3)


class TestSearchDeliveryDateFields(TestCase):
    def setUp(self):
        self.client = login_as_su()

        self.first_asset = create_asset(
            delivery_date=datetime.date(2001, 1, 1),
            sn='1234-1234-1234-1234',
        )

        self.second_asset = create_asset(
            delivery_date=datetime.date(2002, 1, 1),
            sn='1235-1235-1235-1235',
        )

        self.third_asset = create_asset(
            delivery_date=datetime.date(2003, 1, 1),
            sn='1236-1236-1236-1236',
        )

    def test_start_date_is_equal_end_date(self):
        url = '/assets/dc/search?delivery_date_form=%s&delivery_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_start_date_is_less_then_end_date(self):
        url = '/assets/dc/search?delivery_date_form=%s&delivery_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 0)

    def test_find_more_assets_lte_gte(self):
        url = '/assets/dc/search?delivery_date_form=%s&delivery_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

    def test_start_date_is_empty(self):
        url = '/assets/dc/search?delivery_date_form=%s&delivery_date_to=%s' % (
            '', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_end_date_is_empty(self):
        url = '/assets/dc/search?delivery_date_form=%s&delivery_date_to=%s' % (
            '1999-01-01', '')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 3)


class TestSearchRequestDateFields(TestCase):
    def setUp(self):
        self.client = login_as_su()

        self.first_asset = create_asset(
            request_date=datetime.date(2001, 1, 1),
            sn='1234-1234-1234-1234',
        )

        self.second_asset = create_asset(
            request_date=datetime.date(2002, 1, 1),
            sn='1235-1235-1235-1235',
        )

        self.third_asset = create_asset(
            request_date=datetime.date(2003, 1, 1),
            sn='1236-1236-1236-1236',
        )

    def test_start_date_is_equal_end_date(self):
        url = '/assets/dc/search?request_date_from=%s&request_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_start_date_is_less_then_end_date(self):
        url = '/assets/dc/search?request_date_from=%s&request_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 0)

    def test_find_more_assets_lte_gte(self):
        url = '/assets/dc/search?request_date_from=%s&request_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

    def test_start_date_is_empty(self):
        url = '/assets/dc/search?request_date_from=%s&request_date_to=%s' % (
            '', '2001-01-01')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_end_date_is_empty(self):
        url = '/assets/dc/search?request_date_from=%s&request_date_to=%s' % (
            '1999-01-01', '')
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 3)


class TestSearchProductionUseDateFields(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.base_url = '/assets/dc/search'

        self.first_asset = create_asset(
            production_use_date=datetime.date(2001, 1, 1),
            sn='1234-1234-1234-1234',
        )

        self.second_asset = create_asset(
            production_use_date=datetime.date(2002, 1, 1),
            sn='1235-1235-1235-1235',
        )

        self.third_asset = create_asset(
            production_use_date=datetime.date(2003, 1, 1),
            sn='1236-1236-1236-1236',
        )

    def test_start_date_is_equal_end_date(self):
        url = '?production_use_date_from=%s&production_use_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_start_date_is_less_then_end_date(self):
        url = '?production_use_date_from=%s&production_use_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 0)

    def test_find_more_assets_lte_gte(self):
        url = '?production_use_date_from=%s&production_use_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 2)

        self.assertItemsEqual(
            [asset.sn for asset in rows_from_table],
            ['1234-1234-1234-1234', '1235-1235-1235-1235']
        )

    def test_start_date_is_empty(self):
        url = '?production_use_date_from=%s&production_use_date_to=%s' % (
            '', '2001-01-01')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 1)
        self.assertEqual(rows_from_table[0].sn, '1234-1234-1234-1234')

    def test_end_date_is_empty(self):
        url = '?production_use_date_from=%s&production_use_date_to=%s' % (
            '1999-01-01', '')
        content = self.client.get(self.base_url + url)
        self.assertEqual(content.status_code, 200)

        rows_from_table = content.context_data['bob_page'].object_list
        self.assertEqual(len(rows_from_table), 3)
