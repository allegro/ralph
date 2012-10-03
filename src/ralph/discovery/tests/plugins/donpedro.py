# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
import mock

from ralph.discovery.plugins import ssh_aix
from ralph.discovery.models import DeviceType, Device, IPAddress, DiskShare
from ralph.discovery.api import import_device_data
from ralph.discovery.tests.util import MockSSH
from ralph.discovery.tests.plugins.samples.donpedro import data


class DonPedroPluginTest(TestCase):
    def setUp(self):
        ip = '10.10.10.10'
        import_device_data(data, ip)
