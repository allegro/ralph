#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from mock import patch

from ralph.discovery.models import Device, DeviceType, IPAddress, Ethernet
from ralph.discovery.plugins import ssh_ganeti
from ralph.discovery.tests.util import MockSSH


INSTANCES = """
host1.dc1.local   gnt10.dc.local gnt21.dc       -            99:ff:cc:90:22:33
host2.dc1         gnt11.dc       gnt20.dc       -            99:df:cc:90:22:09
host3.dc1         gnt10.dc.local gnt20.dc       127.0.1.32   99:df:cc:90:33:09
host4.dc1         gnt111222.dc   gnt222111.dc   -            99:df:cc:90:33:aa
"""


class SshGanetiTest(TestCase):

    def setUp(self):
        self._create_cluster_master()
        self._create_hypervisors()

    def _create_cluster_master(self):
        self.master_dev = Device.create(
            sn='sn_master_abc_1',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown,
        )
        IPAddress.objects.create(
            hostname='master.dc',
            address='127.0.1.88',
            device=self.master_dev,
        )

    def _create_hypervisors(self):
        dev = Device.create(
            sn='sn_hy_abc_1',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown,
        )
        dev.name = 'gnt-test.dc.local'
        dev.save()
        dev = Device.create(
            sn='sn_hy_abc_2',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown,
        )
        dev.name = 'gnt10.dc.local'
        dev.save()
        dev = Device.create(
            sn='sn_hy_abc_3',
            model_name='SomeDeviceModelName',
            model_type=DeviceType.unknown,
        )
        dev.name = 'gnt11.dc'
        dev.save()

    def test_get_device(self):
        device = ssh_ganeti.get_device('master.dc')
        self.assertEqual(device.id, self.master_dev.id)
        device = ssh_ganeti.get_device('master2.dc', 'ziew')
        self.assertEqual(device, 'ziew')

    def test_get_master_hostname(self):
        ssh = MockSSH([
            (
                '/usr/sbin/gnt-cluster getmaster',
                'master.dc',
            )
        ])
        master_hostname = ssh_ganeti.get_master_hostname(ssh)
        self.assertEquals(master_hostname, 'master.dc')
        ssh = MockSSH([
            (
                '/usr/sbin/gnt-cluster getmaster',
                '',
            )
        ])
        with self.assertRaises(ssh_ganeti.Error):
            master_hostname = ssh_ganeti.get_master_hostname(ssh)

    def test_get_instances(self):
        ssh = MockSSH([
            (
                '/usr/sbin/gnt-instance list -o name,pnode,snodes,ip,mac '
                '--no-headers',
                INSTANCES,
            )
        ])
        instances = list(ssh_ganeti.get_instances(ssh))
        self.assertEquals(instances, [
            (u'host1.dc1.local', u'gnt10.dc.local', None, u'99FFCC902233'),
            (u'host2.dc1', u'gnt11.dc', None, u'99DFCC902209'),
            (u'host3.dc1', u'gnt10.dc.local', u'127.0.1.32', u'99DFCC903309'),
            (u'host4.dc1', u'gnt111222.dc', None, u'99DFCC9033AA'),
        ])

    def test_run_ssh_ganeti(self):
        ssh = MockSSH([
            (
                '/usr/sbin/gnt-cluster getmaster',
                'master.dc',
            ),
            (
                '/usr/sbin/gnt-instance list -o name,pnode,snodes,ip,mac '
                '--no-headers',
                INSTANCES,
            )
        ])
        with patch(
            'ralph.discovery.plugins.ssh_ganeti._connect_ssh',
            lambda ip: ssh,
        ):
            ssh_ganeti.run_ssh_ganeti('127.0.1.88')
        master_ip = IPAddress.objects.get(address='127.0.1.88')
        hypervisor_1 = Device.objects.get(sn='sn_hy_abc_2')
        hypervisor_2 = Device.objects.get(sn='sn_hy_abc_3')
        dev_1 = Ethernet.objects.get(mac='99FFCC902233').device
        dev_2 = Ethernet.objects.get(mac='99DFCC902209').device
        dev_3 = Ethernet.objects.get(mac='99DFCC903309').device
        dev_4 = Ethernet.objects.get(mac='99DFCC9033AA').device
        self.assertEquals(dev_1.parent_id, hypervisor_1.id)
        self.assertEquals(dev_1.name, 'host1.dc1.local')
        self.assertEquals(dev_1.management.id, master_ip.id)
        self.assertEquals(dev_2.parent_id, hypervisor_2.id)
        self.assertEquals(dev_2.name, 'host2.dc1')
        self.assertEquals(dev_2.management.id, master_ip.id)
        self.assertEquals(dev_3.parent_id, hypervisor_1.id)
        self.assertEquals(dev_3.name, 'host3.dc1')
        self.assertEquals(dev_3.management.id, master_ip.id)
        self.assertTrue(
            dev_3.ipaddress_set.filter(address='127.0.1.32').exists(),
        )
        self.assertFalse(dev_4.parent_id)
