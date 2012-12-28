# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import (
    Device,
    DeviceType,
    IPAddress,
)
from ralph.deployment.models import Deployment
from ralph.deployment.plugins.clean import clean

class CleanPluginTest(TestCase):
    def setUp(self):
        device = Device.create(
            ethernets=[('', 'deadbeefcafe', 0)],
            model_name='HAL 9000',
            model_type=DeviceType.unknown,
            remarks="I'm sorry, Dave.",
        )
        self.deployment = Deployment(
            hostname='discovery.one',
            ip='127.0.0.1',
            mac='deadbeefcafe',
            device=device,
            preboot=None,
            venture=None,
            venture_role=None,
        )
        self.deployment.save()
        self.ip = IPAddress(address='127.0.0.1', device=device)
        self.ip.save()

    def test_clean_plugin(self):
        clean(self.deployment.id)
        device = Device.objects.get(id=self.deployment.device.id)
        self.assertEqual(
            device.remarks,
            "-- Remarks below are for old role -/- from 2012-12-28 --\n"
            "I'm sorry, Dave.",
        )
        self.assertFalse(device.ipaddress_set.exists())
