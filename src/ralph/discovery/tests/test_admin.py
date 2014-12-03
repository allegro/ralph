# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.discovery.tests.util import DeviceFactory
from ralph.ui.tests.global_utils import login_as_su
from ralph.ui.widgets import ReadOnlyWidget, ReadOnlySelectWidget
from ralph_assets.tests.utils.assets import DCAssetFactory, DeviceInfoFactory


BASE_DEV_FORM_FIELDS = [
    'deleted', 'uptime_seconds', 'uptime_timestamp', 'name', 'name2', 'parent',
    'logical_parent', 'model', 'sn', 'barcode', 'remarks', 'boot_firmware',
    'hard_firmware', 'diag_firmware', 'mgmt_firmware', 'price',
    'purchase_date', 'deprecation_date', 'cached_price', 'cached_cost',
    'warranty_expiration_date', 'support_expiration_date', 'support_kind',
    'deprecation_kind', 'margin_kind', 'chassis_position', 'position',
    'venture', 'management', 'role', 'venture_role', 'dc', 'rack', 'verified',
    'service', 'device_environment',
]


class DeviceAdminTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.device = DeviceFactory()
        self.url = reverse(
            'admin:discovery_device_change', args=(self.device.id,),
        )

    def test_base_fields(self):
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data['adminform'].form.fields.keys(),
            BASE_DEV_FORM_FIELDS,
        )
        self.assertFalse(isinstance(
            response.context_data['adminform'].form.fields['dc'].widget,
            ReadOnlyWidget,
        ))
        self.assertFalse(isinstance(
            response.context_data['adminform'].form.fields['rack'].widget,
            ReadOnlyWidget,
        ))
        self.assertFalse(isinstance(
            response.context_data['adminform'].form.fields['parent'].widget,
            ReadOnlySelectWidget,
        ))
        self.assertFalse(isinstance(
            response.context_data[
                'adminform'
            ].form.fields['management'].widget,
            ReadOnlySelectWidget,
        ))

    def test_base_fields_when_asset_is_assigned(self):
        """Asset has not is_blade flag -> edition is not possible"""
        asset = DCAssetFactory(
            device_info=DeviceInfoFactory(
                ralph_device_id=self.device.id,
            ),
        )
        asset.model.category.is_blade = False
        asset.model.category.save()
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data['adminform'].form.fields.keys(),
            BASE_DEV_FORM_FIELDS,
        )
        self.assertTrue(isinstance(
            response.context_data['adminform'].form.fields['dc'].widget,
            ReadOnlyWidget,
        ))
        self.assertTrue(isinstance(
            response.context_data['adminform'].form.fields['rack'].widget,
            ReadOnlyWidget,
        ))
        self.assertTrue(isinstance(
            response.context_data['adminform'].form.fields['parent'].widget,
            ReadOnlySelectWidget,
        ))
        self.assertTrue(isinstance(
            response.context_data[
                'adminform'
            ].form.fields['management'].widget,
            ReadOnlySelectWidget,
        ))


class IPAddressAdminTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.device = DeviceFactory()
        self.url = '/admin/discovery/ipaddress/add/'
        self.url = reverse('admin:discovery_ipaddress_add')

    def _make_request(self):
        return self.client.post(
            self.url,
            {
                '-1-TOTAL_FORMS': 0,
                '-1-INITIAL_FORMS': 0,
                '-1-MAX_NUM_FORMS': 0,
                'address': '127.0.0.1',
                'device': self.device.id,
                'is_management': True,
            },
            follow=True,
        )

    def test_device_without_asset_validation(self):
        response = self._make_request()
        self.assertFalse(response.context_data['adminform'].form.is_valid())
        self.assertEqual(
            response.context_data['adminform'].form.non_field_errors(), [],
        )

    def test_device_with_asset_validation(self):
        asset = DCAssetFactory(
            device_info=DeviceInfoFactory(
                ralph_device_id=self.device.id,
            ),
        )
        asset.model.category.is_blade = False
        asset.model.category.save()
        response = self._make_request()
        self.assertFalse(response.context_data['adminform'].form.is_valid())
        msg = response.context_data['adminform'].form.non_field_errors()[0]
        self.assertTrue('You can not assign management IP address' in msg)
