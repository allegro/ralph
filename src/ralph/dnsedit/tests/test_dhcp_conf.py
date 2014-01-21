# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from powerdns.models import Domain, Record

from ralph.dnsedit.models import DHCPEntry, DHCPServer, DNSServer
from ralph.dnsedit.dhcp_conf import (
    generate_dhcp_config,
    generate_dhcp_config_head,
)
from ralph.discovery.models import (
    DataCenter,
    Device,
    Ethernet,
    IPAddress,
    Network,
)
from ralph.deployment.models import Deployment


def _sanitize_dhcp_config(config):
    # remove first and last line from config
    return '\n'.join(config.splitlines()[1:-1])


class DHCPConfTest(TestCase):
    def setUp(self):
        self.dc1 = DataCenter.objects.create(
            name='dc1',
            next_server='10.20.30.40',
            domain='dc1',
        )
        self.dc2 = DataCenter.objects.create(name='dc2', domain='dc2')
        self.domain1 = Domain.objects.create(
            name='dc1.local',
            type='MASTER',
        )
        self.domain2 = Domain.objects.create(
            name='dc2.local',
            type='MASTER',
        )
        self.network1 = Network.objects.create(
            name='net1.dc1',
            address='127.0.0.0/24',
            data_center=self.dc1,
            dhcp_broadcast=True,
            gateway='127.0.0.255',
        )
        self.network2 = Network.objects.create(
            name='net1.dc2',
            address='10.20.1.0/24',
            data_center=self.dc2,
            dhcp_broadcast=True,
            gateway='10.20.1.255',
        )
        DNSServer.objects.create(
            ip_address='10.20.30.1',
            is_default=True,
        )
        DNSServer.objects.create(
            ip_address='10.20.30.2',
            is_default=True,
        )
        self.custom_dns_1 = DNSServer.objects.create(
            ip_address='10.20.30.3',
            is_default=False,
        )
        self.custom_dns_2 = DNSServer.objects.create(
            ip_address='10.20.30.4',
            is_default=False,
        )
        self.network2.custom_dns_servers.add(self.custom_dns_1)
        self.network2.custom_dns_servers.add(self.custom_dns_2)

    def test_basic_entry(self):
        DHCPEntry.objects.create(ip='127.0.0.1', mac='deadbeefcafe')
        Record.objects.create(
            name='1.0.0.127.in-addr.arpa',
            type='PTR',
            content='sample1.dc1',
            domain=self.domain1,
        )
        DHCPEntry.objects.create(ip='10.10.0.1', mac='deadbeefcaff')
        Record.objects.create(
            name='1.0.10.10.in-addr.arpa',
            type='PTR',
            content='sample2.dc1',
            domain=self.domain1,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1'),
        )
        # sample2.dc don't have defined network
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }',
        )
        # dhcp broadcast is disable
        self.network1.dhcp_broadcast = False
        self.network1.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1'),
        )
        self.assertEqual(config, '')

    def test_dc_entry(self):
        DHCPEntry.objects.create(ip='127.0.0.1', mac='deadbeefcafe')
        Record.objects.create(
            name='1.0.0.127.in-addr.arpa',
            type='PTR',
            content='sample1.dc1',
            domain=self.domain1,
        )
        DHCPEntry.objects.create(ip='10.20.1.1', mac='deadbeefcaf1')
        Record.objects.create(
            name='1.1.20.10.in-addr.arpa',
            type='PTR',
            content='sample1.dc2',
            domain=self.domain2,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1', dc=self.dc2),
        )
        self.assertEqual(
            config,
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )

    def test_deployment_entry(self):
        DHCPEntry.objects.create(ip='127.0.0.1', mac='deadbeefcafe')
        Record.objects.create(
            name='1.0.0.127.in-addr.arpa',
            type='PTR',
            content='sample1.dc1',
            domain=self.domain1,
        )
        device = Device.objects.create(sn='sn123')
        Deployment.objects.create(
            ip='127.0.0.1',
            mac='deadbeefcafe',
            device=device,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; next-server 10.20.30.40; }',
        )

    def test_no_ptr_entry(self):
        DHCPEntry.objects.create(ip='127.0.0.1', mac='deadbeefcafe')
        DHCPEntry.objects.create(ip='10.10.0.1', mac='deadbeefcaff')
        device = Device.objects.create(sn='sn123')
        Ethernet.objects.create(
            mac='deadbeefcafe', label="eth0", device=device,
        )
        IPAddress.objects.create(
            address='127.0.0.1',
            hostname='name-from-ip.dc1',
            device=device,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            'host name-from-ip.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }',
        )

    def test_networks_configs(self):
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            """shared-network "net1.dc1" {
    subnet 127.0.0.0 netmask 255.255.255.0 {
        option routers 127.0.0.255;
        option domain-name "dc1";
        option domain-name-servers 10.20.30.1,10.20.30.2;
        deny unknown-clients;
    }
}

shared-network "net1.dc2" {
    subnet 10.20.1.0 netmask 255.255.255.0 {
        option routers 10.20.1.255;
        option domain-name "dc2";
        option domain-name-servers 10.20.30.3,10.20.30.4;
        deny unknown-clients;
    }
}"""
        )
        self.network1.dhcp_broadcast = False
        self.network1.save()
        self.network2.dhcp_config = 'SAMPLE ADDITIONAL CONFIG'
        self.network2.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            """shared-network "net1.dc2" {
    subnet 10.20.1.0 netmask 255.255.255.0 {
        option routers 10.20.1.255;
        option domain-name "dc2";
        option domain-name-servers 10.20.30.3,10.20.30.4;
        deny unknown-clients;
SAMPLE ADDITIONAL CONFIG
    }
}"""
        )

    def test_additional_dhcp_server_config(self):
        DHCPServer.objects.create(
            ip='127.0.1.1',
            dhcp_config='SAMPLE DHCP CONFIG',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            """SAMPLE DHCP CONFIG


shared-network "net1.dc1" {
    subnet 127.0.0.0 netmask 255.255.255.0 {
        option routers 127.0.0.255;
        option domain-name "dc1";
        option domain-name-servers 10.20.30.1,10.20.30.2;
        deny unknown-clients;
    }
}

shared-network "net1.dc2" {
    subnet 10.20.1.0 netmask 255.255.255.0 {
        option routers 10.20.1.255;
        option domain-name "dc2";
        option domain-name-servers 10.20.30.3,10.20.30.4;
        deny unknown-clients;
    }
}"""
        )

    def test_dc_networks_configs(self):
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(server_address='127.0.1.1', dc=self.dc2),
        )
        self.assertEqual(
            config,
            """shared-network "net1.dc2" {
    subnet 10.20.1.0 netmask 255.255.255.0 {
        option routers 10.20.1.255;
        option domain-name "dc2";
        option domain-name-servers 10.20.30.3,10.20.30.4;
        deny unknown-clients;
    }
}"""
        )

    def test_no_domain_networks_configs(self):
        self.dc2.domain = None
        self.dc2.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(server_address='127.0.1.1'),
        )
        self.assertEqual(
            config,
            """shared-network "net1.dc1" {
    subnet 127.0.0.0 netmask 255.255.255.0 {
        option routers 127.0.0.255;
        option domain-name "dc1";
        option domain-name-servers 10.20.30.1,10.20.30.2;
        deny unknown-clients;
    }
}"""
        )

