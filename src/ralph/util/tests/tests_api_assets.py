# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.deployment.util import _create_device
from ralph.util.api_assets import get_devices

class API_assetsTest(TestCase):
	def setUp(self):
		data = {
			'mac': '18:03:73:b1:85:93',
			'rack_sn': 'rack_sn_123_321_1',
			'management_ip': '10.20.10.1',
			'hostname': 'test123.dc',
			'ip': '10.22.10.1',
		}
		_create_device(data)

	def test_get_devices(self):
		device = get_devices().next()
		self.assertEqual(device['device_id'], 1)
		self.assertEqual(device['name'], 'test123.dc')
		self.assertEqual(device['deleted'], False)
		self.assertEqual(device['support_kind'], None)
		self.assertEqual(device['barcode'], None)
		self.assertEqual(device['remarks'], '')
		self.assertEqual(device['purchase_date'], None)
		self.assertEqual(device['price'], None)
		self.assertEqual(device['sn'], None)

