# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.assets.models_assets import Asset, AssetType, AssetStatus
from ralph.assets.tests.util import (
    create_model, create_warehouse, SCREEN_ERROR_MESSAGES
)
from ralph.ui.tests.helper import login_as_su


class TestMultivalueFields(TestCase):
    def setUp(self):
        self.client = login_as_su()
        self.warehouse = create_warehouse()
        self.model = create_model()
        self.addform = '/assets/dc/add/device/'

    def test_add_form_testing_sn_and_barcode(self):
        """
        Test multivalue fields.

        Scenario:
        1. Add many SNs and barcodes in different forms.
        2. Doesn't add empty serial number
        3. Test relationship between SNs and barcodes.
        4. Verity names with white spaces (SNs, barcode).
        """

        test_data = [
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='sn1_1, sn2_1, sn1_1',
                remarks='asset1',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='sn1_2, , , sn2_2',
                remarks='asset2',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='sn1_3, ,, sn2_3',
                remarks='asset3',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='sn1_4, ns2_4 \n sn3_4',
                remarks='asset4',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='name with white spaces, 0000-0000-0000-0000',
                remarks='asset5',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='',
                barcode='any',
                remarks='asset6',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber1',
                barcode='any1, any2',
                remarks='asset7',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber2, serialnumber3',
                barcode='any3',
                remarks='asset8',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber4, serialnumber5',
                barcode='any4, any 5',
                remarks='asset9',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber6, serialnumber7, serialnumber8',
                barcode='any6 , , any 7',
                remarks='asset10',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber9, serialnumber10, serialnumber11',
                barcode='any8 , \n, any9',
                remarks='asset11',
                size=1,
            ),
            dict(
                type=AssetType.data_center,
                model=self.model.id,
                support_period='1',
                support_type='standard',
                invoice_date='2001-01-02',
                warehouse=self.warehouse.id,
                status=AssetStatus.new,
                sn='serialnumber12',
                barcode='barcode1',
                remarks='asset12',
                size=1,
            ),
        ]
        # Add form testing
        for test in test_data:
            post = self.client.post(self.addform, test)
            added_assets = Asset.objects.filter(remarks=test['remarks'])
            if test['remarks'] == 'asset1':
                self.assertEqual(post.status_code, 200)
                self.assertFormError(
                    post, 'asset_form', 'sn',
                    SCREEN_ERROR_MESSAGES['duplicated_sn_in_field']
                )
            elif test['remarks'] == 'asset2':
                self.assertEqual(post.status_code, 302)
                self.assertEqual(len(added_assets), 2)
                self.assertEqual(
                    ['sn1_2', 'sn2_2'], [asset.sn for asset in added_assets]
                )
            elif test['remarks'] == 'asset3':
                self.assertEqual(post.status_code, 302)
                self.assertEqual(len(added_assets), 2)
                self.assertEqual(
                    ['sn1_3', 'sn2_3'], [asset.sn for asset in added_assets]
                )
            elif test['remarks'] == 'asset4':
                self.assertEqual(post.status_code, 302)
                self.assertEqual(len(added_assets), 3)
                self.assertEqual(
                    ['sn1_4', 'ns2_4', 'sn3_4'],
                    [asset.sn for asset in added_assets]
                )
            elif test['remarks'] == 'asset5':
                self.assertFormError(
                    post, 'asset_form', 'sn',
                    SCREEN_ERROR_MESSAGES['contain_white_character']
                )
            elif test['remarks'] in ['asset9', 'asset10']:
                self.assertEqual(post.status_code, 200)
                self.assertFormError(
                    post, 'asset_form', 'barcode',
                    SCREEN_ERROR_MESSAGES['contain_white_character']
                )
            elif test['remarks'] == 'asset6':
                self.assertFormError(
                    post, 'asset_form', 'sn',
                    SCREEN_ERROR_MESSAGES['django_required']
                )
            elif test['remarks'] in ['asset6', 'asset7', 'asset 8', 'asset11']:
                self.assertEqual(post.status_code, 200)
                self.assertFormError(
                    post, 'asset_form', 'barcode',
                    SCREEN_ERROR_MESSAGES['count_sn_and_bc']
                )
            elif test['remarks'] == 'asset9':
                self.assertEqual(post.status_code, 200)
                self.assertFormError(
                    post, 'asset_form', 'barcode',
                    SCREEN_ERROR_MESSAGES['contain_white_character']
                )
            elif test['remarks'] == 'asset12':
                duplicate = dict(
                    type=AssetType.data_center,
                    model=self.model.id,
                    support_period='1',
                    support_type='standard',
                    invoice_date='2001-01-02',
                    warehouse=self.warehouse.id,
                    status=AssetStatus.new,
                    sn='serialnumber13',
                    barcode='barcode1',
                    remarks='asset12',
                    size=1,
                )
                post = self.client.post(self.addform, duplicate)
                self.assertEqual(post.status_code, 200)
                self.assertFormError(
                    post, 'asset_form', 'barcode',
                    SCREEN_ERROR_MESSAGES['barcode_already_exist'] + 'barcode1'
                )
        empty_sn = Asset.objects.filter(sn=' ')
        self.assertEqual(len(empty_sn), 0)
        empty_sn = Asset.objects.filter(barcode=' ')
        self.assertEqual(len(empty_sn), 0)
