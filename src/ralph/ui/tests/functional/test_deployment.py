# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.discovery.tests.util import DeviceFactory
from ralph.ui.tests.global_utils import login_as_su
from ralph_assets.tests.utils.assets import DCAssetFactory, DeviceInfoFactory


class CreateDeviceFormTest(TestCase):

    def setUp(self):
        self.client = login_as_su()

    def test_position_edit_blocking(self):
        url = reverse(
            'racks', kwargs={
                'rack': '-', 'details': 'add_device', 'device': '',
            },
        )
        dev = DeviceFactory()
        asset = DCAssetFactory(
            device_info=DeviceInfoFactory(
                ralph_device_id=dev.id,
            ),
        )
        post_data = {
            'asset': asset.id,
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertFalse(response.context['form'].is_valid())
        from ralph.ui.widgets import ReadOnlyWidget
        self.assertTrue(
            isinstance(
                response.context['form'].fields['chassis_position'].widget,
                ReadOnlyWidget,
            ),
        )
        self.assertTrue(
            isinstance(
                response.context['form'].fields['position'].widget,
                ReadOnlyWidget,
            ),
        )
