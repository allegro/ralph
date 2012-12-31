# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from ralph.discovery.models import (
    Device,
    DeviceType,
    IPAddress,
    DiskShare,
    DiskShareMount,
    OperatingSystem,
    Software,
    ComponentModel,
    ComponentType,
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
        share_model = ComponentModel(type=ComponentType.share, name="share")
        share_model.save()
        share = DiskShare(wwn='x'*33, device=device, model=share_model)
        share.save()
        DiskShareMount(share=share, device=device).save()
        OperatingSystem.create(os_name='GladOS', dev=device, family='')
        Software.create(dev=device, model_name='soft', path='/', family='')

    def test_clean_plugin(self):
        clean(self.deployment.id)
        device = Device.objects.get(id=self.deployment.device.id)
        self.assertEqual(
            device.remarks,
            "-- Remarks below are for old role -/- from %s --\n"
            "I'm sorry, Dave." % datetime.date.today().strftime('%Y-%m-%d'),
        )
        self.assertFalse(device.ipaddress_set.exists())
        self.assertFalse(device.diskshare_set.exists())
        self.assertFalse(device.disksharemount_set.exists())
        self.assertFalse(device.software_set.exists())
        self.assertFalse(device.operatingsystem_set.exists())
