# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.assets.models import AssetType, AssetSource, AssetStatus
from ralph.assets.tests.util import (
    create_asset, create_model, SCREEN_ERROR_MESSAGES
)
from ralph.ui.tests.helper import login_as_su


class TestValidations(TestCase):
    """Scenario:
    1. test validation (required fields) add, edit
    2. test wrong data in fields
    """

    def setUp(self):
        self.client = login_as_su()

        self.first_asset = create_asset(
            sn='1234-1234-1234-1234'
        )

        self.asset_with_duplicated_sn = create_asset(
            sn='1111-1111-1111-1111'
        )

        # Prepare required fields (formset_name, field_name)
        self.required_fields = [
            ('asset_form', 'model'),
            ('asset_form', 'support_period'),
            ('asset_form', 'support_type'),
            ('asset_form', 'warehouse'),
            ('asset_form', 'sn'),
        ]

        self.model1 = create_model()

    def test_try_send_empty_add_form(self):
        send_post = self.client.post('/assets/back_office/add/device/', {})
        self.assertEqual(send_post.status_code, 200)

        for field in self.required_fields:
            self.assertFormError(
                send_post, field[0], field[1], 'This field is required.'
            )

    def test_try_send_empty_edit_form(self):
        send_post = self.client.post('/assets/dc/edit/device/1/', {})
        self.assertEqual(send_post.status_code, 200)

        for field in self.required_fields:
            self.assertFormError(
                send_post, field[0], field[1], 'This field is required.'
            )

    def test_invalid_field_value(self):
        # instead of integers we send strings, error should be thrown
        url = '/assets/back_office/add/device/'
        post_data = {
            'support_period': 'string',
            'size': 'string',
            'invoice_date': 'string',
        }
        send_post = self.client.post(url, post_data)
        self.assertEqual(send_post.status_code, 200)

        # other fields error
        self.assertFormError(
            send_post, 'asset_form', 'support_period', 'Enter a whole number.'
        )
        self.assertFormError(
            send_post, 'device_info_form', 'size', 'Enter a whole number.'
        )
        self.assertFormError(
            send_post, 'asset_form', 'invoice_date', 'Enter a valid date.'
        )

    def test_send_wrong_data_in_bulkedit_form(self):
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.first_asset.id, self.asset_with_duplicated_sn.id)
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,  # Select field; value = 1
            'form-0-model': self.model1.name,  # u'Model1'
            'form-0-invoice_no': 'Invoice No1',
            'form-0-order_no': 'Order No1',
            'form-0-invoice_date': 'wrong_field_data',
            'form-0-sn': '1111-1111-1111-1111',
            'form-0-barcode': 'bc-1234',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider 1',
            'form-0-status': AssetStatus.in_progress.id,  # Select field; value = 2
            'form-0-source': AssetSource.shipment.id,  # Select field; value = 1
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,  # Select field; value = 1
            'form-1-model': '',
            'form-1-invoice_no': 'Invoice No2',
            'form-1-order_no': 'Order No2',
            'form-1-invoice_date': '2011-02-03',
            'form-1-sn': '2222-2222-2222-2222',
            'form-1-barcode': 'bc-12345',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider2',
            'form-1-status': '',
            'form-1-source': '',
        }
        send_post_with_empty_fields = self.client.post(url, post_data)

        # Try to send post with empty field send_post should be false
        try:
            self.assertRedirects(
                send_post_with_empty_fields,
                url,
                status_code=302,
                target_status_code=200,
            )
            send_post = True
        except AssertionError:
            send_post = False
        # If not here is error msg
        self.assertFalse(send_post, 'Empty fields was send!')

        # Find what was wrong
        bulk_data = [
            dict(
                row=0, field='invoice_date', error='Enter a valid date.',
            ),
            dict(
                row=0, field='sn', error='Asset with this Sn already exists.',
            ),
            dict(
                row=1, field='model', error='This field is required.',
            ),
            dict(
                row=1, field='source', error='This field is required.',
            ),
            dict(
                row=1, field='status', error='This field is required.',
            )
        ]
        for bulk in bulk_data:
            formset = send_post_with_empty_fields.context_data['formset']
            self.assertEqual(
                formset[bulk['row']]._errors[bulk['field']][0],
                bulk['error']
            )

        # if sn was duplicated, the message should be shown on the screen
        msg = SCREEN_ERROR_MESSAGES['duplicated_sn_or_bc']
        self.assertTrue(msg in send_post_with_empty_fields.content)
