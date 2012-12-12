# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from ralph.assets.models_assets import AssetStatus
from ralph.assets.tests.util import (
    create_asset, client_get, DEFAULT_ASSET_DATA
)
from ralph.ui.tests.helper import login_as_su


class TestDataDisplay(TestCase):
    """Test check if data from database are displayed on screen"""

    def setUp(self):
        self.client = login_as_su()
        self.correct_data = dict(
            barcode='123456789',
            invoice_no='Invoice #1',
            order_no='Order #1',
            invoice_date=datetime.date(2001, 1, 1),
            status=AssetStatus.new,
        )
        self.new_asset = create_asset(self.correct_data)
        self.correct_data.update(DEFAULT_ASSET_DATA)

    def test_display_data_in_table(self):
        get_data_from_table = client_get(url='/assets/dc/search', follow=True)
        self.assertEqual(get_data_from_table.status_code, 200)

        # Test if data from database are displayed in correct row.
        self.assertItemsEqual(self.correct_data, self.new_asset)
