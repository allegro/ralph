# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from ralph.assets.models_assets import (AssetStatus, AssetType)
from ralph.assets.tests.util import create_asset
from ralph.ui.tests.helper import login_as_su


class TestDataDisplay(TestCase):
    """Test check if data from database are displayed on screen"""

    def setUp(self):
        self.client = login_as_su()
        asset_fields = dict(
            barcode='123456789',
            invoice_no='Invoice #1',
            order_no='Order #1',
            invoice_date=datetime.date(2001, 1, 1),
            sn='0000-0000-0000-0000',
        )
        self.asset = create_asset(**asset_fields)

    def test_display_data_in_table(self):
        get_search_page = self.client.get('/assets/dc/search')
        self.assertEqual(get_search_page.status_code, 200)

        # Test if data from database are displayed in correct row.
        first_table_row = get_search_page.context_data['page'][0]
        self.assertEqual(self.asset, first_table_row)
        self.assertItemsEqual(
            [
                first_table_row.barcode,
                first_table_row.invoice_no,
                first_table_row.order_no,
                unicode(first_table_row.invoice_date),
                first_table_row.sn,
                AssetType.name_from_id(first_table_row.type),
                AssetStatus.name_from_id(first_table_row.status),
                first_table_row.model.name,
                first_table_row.warehouse.name,
            ],
            [
                u'123456789',
                u'Invoice #1',
                u'Order #1',
                u'2001-01-01',
                u'0000-0000-0000-0000',
                u'Model1',
                'data_center',
                'new',
                'Warehouse',
            ]
        )
