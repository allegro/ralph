# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.assets.models_assets import AssetType, AssetStatus, AssetSource
from ralph.assets.tests.util import create_asset, create_model
from ralph.ui.tests.helper import login_as_su


class TestBulkEdit(TestCase):
    """Test forms for may actions

    Scenario:
    1. Add two assets
    2. Chceck if data was saved
    """

    def setUp(self):
        self.client = login_as_su()
        self.asset = create_asset(
            sn='1111-1111-1111-1111'
        )
        self.asset1 = create_asset(
            sn='2222-2222-2222-2222'
        )
        self.model = create_model()
        self.model1 = create_model(name='Model2')

    def test_edit_via_bulkedit_form(self):
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.asset.id, self.asset1.id)
        content = self.client.get(url)
        self.assertEqual(content.status_code, 200)

        # Prepare data for send via form
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,
            'form-0-model': self.model.id,
            'form-0-invoice_no': 'Invoice No1',
            'form-0-order_no': 'Order No1',
            'form-0-invoice_date': '2012-02-02',
            'form-0-sn': '3333-3333-3333-3333',
            'form-0-barcode': 'bc-3333-3333-3333-3333',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider1',
            'form-0-status': AssetStatus.in_progress.id,
            'form-0-source': AssetSource.shipment.id,
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,
            'form-1-model': self.model1.id,
            'form-1-invoice_no': 'Invoice No2',
            'form-1-order_no': 'Order No2',
            'form-1-invoice_date': '2011-02-03',
            'form-1-sn': '4444-4444-4444-4444',
            'form-1-barcode': 'bc-4444-4444-4444-4444',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider2',
            'form-1-status': AssetStatus.waiting_for_release.id,
            'form-1-source': AssetSource.shipment.id,
        }
        post = self.client.post(url, post_data, follow=True)

        # if everything is ok, server return response code = 302, and
        # redirect as to /assets/dc/search given response code 200
        self.assertRedirects(
            post, url, status_code=302, target_status_code=200,
        )

        # Simulate reopening bulkedit form to check if data were written
        new_view = self.client.get(url)
        fields = new_view.context['formset'].queryset

        correct_data = [
            dict(
                model=unicode(self.model),
                invoice_no='Invoice No1',
                order_no='Order No1',
                invoice_date='2012-02-02',
                support_period=24,
                support_type='standard1',
                provider='Provider1',
                status=AssetStatus.in_progress.id,
                sn='3333-3333-3333-3333',
                barcode='bc-3333-3333-3333-3333',
            ),
            dict(
                model=unicode(self.model1),
                invoice_no='Invoice No2',
                order_no='Order No2',
                invoice_date='2011-02-03',
                support_period=48,
                support_type='standard2',
                provider='Provider2',
                status=AssetStatus.waiting_for_release.id,
                sn='4444-4444-4444-4444',
                barcode='bc-4444-4444-4444-4444',
            )
        ]
        counter = 0
        for data in correct_data:
            for key in data.keys():
                self.assertEqual(
                    unicode(getattr(fields[counter], key)), unicode(data[key])
                )
            counter += 1
            # Find success message

        find = []
        i = 0
        msg_error = 'Changes saved.'
        for i in range(len(post.content)):
            if post.content.startswith(msg_error, i - 1):
                find.append(i)
        self.assertEqual(len(find), 1)
