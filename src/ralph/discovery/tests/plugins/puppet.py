# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import (Device, DeviceType, OperatingSystem)
from ralph.discovery.tests.plugins.samples.puppet import data, data_second

from ralph.discovery.plugins.puppet.facts import (
    handle_facts_os, handle_facts_packages)


class PuppetPluginTest(TestCase):
    """Try to import puppet facter data, and make OperatingSystem component"""
    def setUp(self):
        self.dev = Device.create(
            sn='device', model_type=DeviceType.virtual_server,
            model_name='device'
        )
        self.dev.save()
        self.dev2 = Device.create(
            sn='device2', model_type=DeviceType.virtual_server,
            model_name='device2'
        )

    def test_handle_facts_os(self):
        handle_facts_os(self.dev, data, is_virtual=True)
        os = OperatingSystem.objects.get(label='CentOS 5.6 2.6.36.2')
        self.assertEqual(os.model.name, 'CentOS 5.6')
        self.assertEqual(os.memory, 1000)
        self.assertEqual(os.cores_count, 1)
        self.assertEqual(os.model.get_type_display(), 'operating system')

    def test_handle_facts_packages(self):
        handle_facts_packages(self.dev, data['packages_data'])
        handle_facts_packages(self.dev2, data_second['packages_data'])
        handle_facts_packages(self.dev2, data['packages_data'])
        device = Device.objects.get(sn='device')
        device_packages = [
            (x.label, x.version) for x in device.software_set.all()
        ]
        device_packages.sort()
        self.assertListEqual(
            device_packages,
            [('apache2', '2.2.22-1ubuntu1'),
             ('cron', '3.0pl1-120ubuntu4'),
             ('gcc', '4:4.6.3-1ubuntu5'),
             ('mysql-client', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server-5.4', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server-core-5.5', '5.5.28-0ubuntu0.12.04.2'),
             ('python', '2.7.3-0ubuntu2'),
             ('sed', '4.3.1-9')]
        )
        device2 = Device.objects.get(sn='device2')
        device_packages = [
            (x.label, x.version) for x in device2.software_set.all()
        ]
        device_packages.sort()
        self.assertListEqual(
            device_packages,
            [('apache2', '1.2.22-1ubuntu1'),
             ('apache2', '2.2.22-1ubuntu1'),
             ('cron', '3.0pl1-120ubuntu4'),
             ('gcc', '4:4.6.3-1ubuntu5'),
             ('mysql-client', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server-5.4', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server-5.5', '5.5.28-0ubuntu0.12.04.2'),
             ('mysql-server-core-5.5', '5.5.28-0ubuntu0.12.04.2'),
             ('python', '2.7.3-0ubuntu2'),
             ('sed', '4.1.1-9'),
             ('sed', '4.3.1-9')]
        )
