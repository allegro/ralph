# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from django.conf import settings
from django.test import TestCase
import mock

from ralph.discovery.models import (Device, DeviceType, OperatingSystem)
from ralph.discovery.tests.plugins.samples.puppet import (
    facts_db_data, packages_data, packages_data_not_encoded,
    facts_api_data,
)
from ralph.discovery.plugins.puppet.facts import (
    handle_facts_os,
    handle_facts_packages,
    handle_facts_disks,
)
from ralph.discovery.plugins.puppet import PuppetAPIProvider


CURRENT_DIR = settings.CURRENT_DIR


class PuppetAPIProviderTest(TestCase):

    """Try to provide facts from YAML"""

    def test_load(self):
        """Check if yaml is parsed correctly."""
        contents = None
        with open(os.path.join(
                  CURRENT_DIR, 'discovery', 'tests',
                  'plugins', 'samples', 'puppet.yaml')) as yaml_file:
            contents = yaml_file.read()

        with mock.patch(
                'ralph.discovery.plugins.puppet.PuppetAPIProvider'
                '.get_data_for_hostname') as get_data_for_hostname:
            get_data_for_hostname.return_value = contents
            provider = PuppetAPIProvider()
            facts = provider.get_facts([], ['', 's10132.dc2'])
            self.assertItemsEqual(facts, facts_api_data['values'])


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
        handle_facts_os(self.dev, facts_db_data, is_virtual=True)
        os = OperatingSystem.objects.get(label='CentOS 5.6 2.6.36.2')
        self.assertEqual(os.model.name, 'CentOS 5.6')
        self.assertEqual(os.memory, 1000)
        self.assertEqual(os.cores_count, 1)
        self.assertEqual(os.model.get_type_display(), 'operating system')

    def test_handle_facts_disks(self):
        handle_facts_disks(self.dev, facts_db_data)
        # should not find because vendor is in black list
        self.assertFalse(
            self.dev.storage_set.filter(sn='sn_test_1231232').exists()
        )
        # should not find because product is in black list
        self.assertFalse(
            self.dev.storage_set.filter(sn='sn_test_1231233').exists()
        )
        # should not find because size is incorrect
        self.assertFalse(
            self.dev.storage_set.filter(sn='sn_test_1231234').exists()
        )
        disk = self.dev.storage_set.get(sn='sn_test_1231231')
        self.assertEqual(disk.size, 140272)
        self.assertEqual(disk.label, 'FUJITSU MBE2147RC 0103')

    def test_handle_facts_packages(self):
        handle_facts_packages(self.dev, facts_db_data['packages'])
        handle_facts_packages(self.dev2, packages_data_not_encoded['packages'])
        handle_facts_packages(self.dev2, facts_db_data['packages'])
        device = Device.objects.get(sn='device')
        device_packages = [
            (x.label, x.version) for x in device.software_set.all()
        ]
        device_packages.sort()
        self.assertListEqual(
            device_packages,
            [('apache2', '2.2.22'),
             ('cron', '3.0pl1'),
             ('gcc', '4:4.6.3'),
             ('mysql-client', '5.5.28'),
             ('mysql-server', '5.5.28'),
             ('mysql-server-5.4', '5.5.28'),
             ('mysql-server-core-5.5', '5.5.28'),
             ('python', '2.7.3'),
             ('sed', '4.3.1')]
        )
        device2 = Device.objects.get(sn='device2')
        device_packages = [
            (x.label, x.version) for x in device2.software_set.all()
        ]
        device_packages.sort()
        self.assertListEqual(
            device_packages,
            [('apache2', '1.2.22'),
             ('apache2', '2.2.22'),
             ('cron', '3.0pl1'),
             ('gcc', '4:4.6.3'),
             ('mysql-client', '5.5.28'),
             ('mysql-server', '5.5.28'),
             ('mysql-server-5.4', '5.5.28'),
             ('mysql-server-5.5', '5.5.28'),
             ('mysql-server-core-5.5', '5.5.28'),
             ('python', '2.7.3'),
             ('sed', '4.1.1'),
             ('sed', '4.3.1')]
        )
