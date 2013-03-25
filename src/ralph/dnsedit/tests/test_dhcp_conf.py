# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.dhcp_conf import generate_dhcp_config
from ralph.discovery.models import Network, DataCenter, Device
from ralph.deployment.models import Deployment


class DHCPConfTest(TestCase):
    def test_basic_entry(self):
        entry = DHCPEntry(ip='127.0.0.1', mac='deadbeefcafe')
        entry.save()
        config = generate_dhcp_config()
        # remove first line with the date and last line
        config = '\n'.join(config.splitlines()[1:-1])
        self.assertEqual(
            config,
            'host 127.0.0.1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }'
        )

    def test_datacenter_entry(self):
        dc = DataCenter(name='dc1')
        dc.save()
        net = Network(name='net', address='127.0.0.0/24', data_center=dc)
        net.save()
        entry = DHCPEntry(ip='127.0.0.1', mac='deadbeefcafe')
        entry.save()
        config = generate_dhcp_config(dc=dc)
        # remove first line with the date and last line
        config = '\n'.join(config.splitlines()[1:-1])
        self.assertEqual(
            config,
            'host 127.0.0.1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }'
        )

    def test_other_datacenter_entry(self):
        dc = DataCenter(name='dc1')
        dc.save()
        dc2 = DataCenter(name='dc2')
        dc2.save()
        net = Network(name='net', address='127.0.0.0/24', data_center=dc)
        net.save()
        entry = DHCPEntry(ip='127.0.0.1', mac='deadbeefcafe')
        entry.save()
        config = generate_dhcp_config(dc=dc2)
        # remove first line with the date and last line
        config = '\n'.join(config.splitlines()[1:-1])
        self.assertEqual(
            config,
            '',
        )

    def test_network_config_entry(self):
        dc = DataCenter(name='dc1')
        dc.save()
        net = Network(
            name='net',
            address='127.0.0.0/24',
            data_center=dc,
            dhcp_config='ziew',
        )
        net.save()
        entry = DHCPEntry(ip='127.0.0.1', mac='deadbeefcafe')
        entry.save()
        config = generate_dhcp_config(dc=dc, with_networks=True)
        # remove first line with the date and last line
        config = '\n'.join(config.splitlines()[1:-1])
        self.assertEqual(
            config,
            """\
shared-network "net" {
    subnet 127.0.0.0 netmask 255.255.255.0 {
ziew
    }
}

host 127.0.0.1 { fixed-address 127.0.0.1; hardware ethernet DE:AD:BE:EF:CA:FE; }"""
        )

    def test_deployment_entry(self):
        dc = DataCenter(name='dc1', next_server='ziew')
        dc.save()
        net = Network(name='net', address='127.0.0.0/24', data_center=dc)
        net.save()
        entry = DHCPEntry(ip='127.0.0.1', mac='deadbeefcafe')
        entry.save()
        device = Device(sn='ziew')
        device.save()
        deployment = Deployment(
            ip='127.0.0.1',
            mac='deadbeefcafe',
            device=device,
        )
        deployment.save()
        config = generate_dhcp_config(dc=dc)
        # remove first line with the date and last line
        config = '\n'.join(config.splitlines()[1:-1])
        self.assertEqual(
            config,
            'host 127.0.0.1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; next-server ziew; }'
        )
