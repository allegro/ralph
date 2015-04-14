# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.scan.util import get_asset_by_name
from ralph_assets.tests.utils.assets import DCAssetFactory


class GetAssetByNameTest(TestCase):

    def test_success(self):
        asset = DCAssetFactory(sn='sn_123123', barcode='barcode_321321')
        name = 'Some Name - sn_123123 - barcode_321321'
        self.assertEqual(get_asset_by_name(name).id, asset.id)

    def test_improper_asset_name(self):
        DCAssetFactory(sn='sn_123123')
        name = 'Some Name - sn_123123-'
        self.assertIsNone(get_asset_by_name(name))

    def test_asset_params_cleaning(self):
        asset_1 = DCAssetFactory(sn='sn_123123', barcode=None)
        name = 'Some Name - sn_123123 - '
        self.assertEqual(get_asset_by_name(name).id, asset_1.id)
        asset_2 = DCAssetFactory(sn=None, barcode='barcode_321321')
        name = 'Some Name -  - barcode_321321'
        self.assertEqual(get_asset_by_name(name).id, asset_2.id)

    def test_asset_does_not_exist(self):
        DCAssetFactory(sn='sn_123123', barcode='barcode_321321')
        name = 'Some Name - sn_123123 - barcode_321'
        self.assertIsNone(get_asset_by_name(name))
