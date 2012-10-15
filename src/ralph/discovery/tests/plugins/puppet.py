# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import (Device, DeviceType, OperatingSystem)
from ralph.discovery.tests.plugins.samples.puppet import data
from ralph.discovery.plugins.puppet.facts import handle_facts_os


class PuppetPluginTest(TestCase):
    """Try to import puppet facter data, and make OperatingSystem component"""
    def setUp(self):
        self.dev = Device.create(
            sn='device', model_type=DeviceType.virtual_server,
            model_name='device'
        )
        self.dev.save()

    def test_handle_facts_os(self):
        handle_facts_os(self.dev, data, is_virtual=True)
        os = OperatingSystem.objects.get(label='CentOS 5.6 2.6.36.2')
        self.assertEqual(os.model.name, 'CentOS 5.6')
        self.assertEqual(os.memory, 1000)
        self.assertEqual(os.cores_count, 1)
        self.assertEqual(os.model.get_type_display(), u'operating system')

