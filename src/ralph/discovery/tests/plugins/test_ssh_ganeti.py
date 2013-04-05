#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import Device, DeviceType
from ralph.discovery.plugins import ssh_ganeti
from ralph.discovery.tests.plugins.samples.ganeti import raw_data, parsed_data
from ralph.discovery.tests.util import MockSSH


class SshGanetiTest(TestCase):
    def setUp(self):
        self._create_hypervisors()

    def _create_hypervisors(self):
        dev = Device.create(
            sn='sn_hy_abc_1',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        dev.name = 'gnt10.dc'
        dev.save()

    def test_get_instances_list(self):
        ssh = MockSSH([(
            "gnt-instance list -o name,pnode,snodes,ip,mac --no-headers",
            raw_data,
        )])
        instances = list(ssh_ganeti.get_instances_list(ssh))
        self.assertEquals(instances, parsed_data)

    def test_get_hypervisor(self):
        pass
