#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import Device, DeviceType, IPAddress
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
        dev.name = 'gnt-test.dc.local'
        dev.save()
        dev = Device.create(
            sn='sn_hy_abc_2',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        dev.name = 'gnt10.dc.local'
        dev.save()
        dev = Device.create(
            sn='sn_hy_abc_3',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown
        )
        dev.name = 'gnt11.dc'
        dev.save()

    def test_get_instances_list(self):
        ssh = MockSSH([(
            "gnt-instance list -o name,pnode,snodes,ip,mac --no-headers",
            raw_data,
        )])
        instances = list(ssh_ganeti.get_instances_list(ssh))
        self.assertEquals(instances, parsed_data)

    def test_get_hypervisor(self):
        hypervisor = Device.objects.get(sn='sn_hy_abc_1')
        self.assertEquals(
            ssh_ganeti.get_hypervisor('gnt-test.dc', {}).id,
            hypervisor.id,
        )
        self.assertEquals(
            ssh_ganeti.get_hypervisor('gnt-test.dc.local', {}).id,
            hypervisor.id,
        )
        self.assertEquals(
            ssh_ganeti.get_hypervisor('test123', {'test123': 'TEST'}),
            'TEST',
        )
        self.assertFalse(
            ssh_ganeti.get_hypervisor('test321', {'test123': 'TEST'}),
        )

    def test_save_device(self):
        data = {
            'mac': '99FFCC902244',
            'ip': '127.0.1.111',
            'host': 'host123.dc55',
            'secondary_nodes': 'gnt-test-2.dc',
            'primary_node': 'gnt-test.dc'
        }
        hypervisor = Device.objects.get(sn='sn_hy_abc_1')
        ssh_ganeti.save_device(data, {})
        device = Device.objects.get(name='host123.dc55')
        self.assertTrue(
            device.ethernet_set.filter(mac='99FFCC902244').exists(),
        )
        self.assertEquals(device.parent_id, hypervisor.id)
        self.assertTrue(
            IPAddress.objects.filter(
                device=device,
                address='127.0.1.111',
            ).exists(),
        )

    def test_run_ssh_ganeti(self):
        ssh = MockSSH([(
            "gnt-instance list -o name,pnode,snodes,ip,mac --no-headers",
            raw_data,
        )])
        ssh_ganeti.run_ssh_ganeti(ssh)
        hypervisor_1 = Device.objects.get(sn='sn_hy_abc_2')
        hypervisor_2 = Device.objects.get(sn='sn_hy_abc_3')
