# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from powerdns.models import Domain, Record

from ralph.dnsedit.models import DHCPEntry, DHCPServer, DNSServer
from ralph.dnsedit.dhcp_conf import (
    generate_dhcp_config_entries,
    generate_dhcp_config_head,
    generate_dhcp_config_networks,
)
from ralph.discovery.models import (
    DataCenter,
    Device,
    Environment,
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
        self.dc1 = DataCenter.objects.create(name='dc1')
        self.dc2 = DataCenter.objects.create(name='dc2')
        self.dc3 = DataCenter.objects.create(name='dc3')
        self.env1 = Environment.objects.create(
            name='dc1',
            data_center=self.dc1,
            next_server='10.20.30.40',
            domain='dc1',
        )
        self.env2 = Environment.objects.create(
            name='dc2',
            data_center=self.dc2,
            domain='dc2',
        )
        self.env3 = Environment.objects.create(
            name='dc3',
            data_center=self.dc3,
            domain='dc3',
        )
        self.env4 = Environment.objects.create(
            name='dc4',
            data_center=self.dc3,
            domain='dc3',
        )
        self.domain1 = Domain.objects.create(
            name='dc1.local',
            type='MASTER',
        )
        self.domain2 = Domain.objects.create(
            name='dc2.local',
            type='MASTER',
        )
        self.domain3 = Domain.objects.create(
            name='dc3.local',
            type='MASTER',
        )
        self.network1 = Network.objects.create(
            name='net1.dc1',
            address='127.0.0.0/24',
            data_center=self.dc1,
            dhcp_broadcast=True,
            gateway='127.0.0.255',
            environment=self.env1,
        )
        self.network2 = Network.objects.create(
            name='net1.dc2',
            address='10.20.1.0/24',
            data_center=self.dc2,
            dhcp_broadcast=True,
            gateway='10.20.1.255',
            environment=self.env2,
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

    def _setup_additional_networks(self):
        self.network3 = Network.objects.create(
            name='net3.dc2',
            address='10.30.1.0/24',
            data_center=self.dc3,
            dhcp_broadcast=True,
            gateway='10.30.1.255',
            environment=self.env3,
        )
        self.network4 = Network.objects.create(
            name='net4.dc2',
            address='10.40.1.0/24',
            data_center=self.dc3,
            dhcp_broadcast=True,
            gateway='10.40.1.255',
            environment=self.env4,
        )

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
            generate_dhcp_config_entries(),
        )
        # sample2.dc don't have defined network
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }',
        )
        # dhcp broadcast is disabled
        self.network1.dhcp_broadcast = False
        self.network1.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(),
        )
        self.assertEqual(config, '')

    def test_env_entry(self):
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
            generate_dhcp_config_entries(),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(environments=[self.env2]),
        )
        self.assertEqual(
            config,
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(environments=[self.env1, self.env2]),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        self._setup_additional_networks()
        # env3 and env4 networks are empty
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(
                environments=[self.env1, self.env3, self.env4]
            ),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }'
        )
        # add some entries
        DHCPEntry.objects.create(ip='10.30.1.1', mac='deadbeefcaf2')
        Record.objects.create(
            name='1.1.30.10.in-addr.arpa',
            type='PTR',
            content='sample1.dc3',
            domain=self.domain3,
        )
        DHCPEntry.objects.create(ip='10.40.1.1', mac='deadbeefcaf3')
        Record.objects.create(
            name='1.1.40.10.in-addr.arpa',
            type='PTR',
            content='sample2.dc3',
            domain=self.domain3,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(
                environments=[self.env1, self.env3, self.env4]
            )
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample1.dc3 { fixed-address 10.30.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F2; }\n'
            'host sample2.dc3 { fixed-address 10.40.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F3; }'
        )

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
            generate_dhcp_config_entries(data_centers=[self.dc1]),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }'
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(data_centers=[self.dc2]),
        )
        self.assertEqual(
            config,
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(data_centers=[self.dc1, self.dc2]),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample1.dc2 { fixed-address 10.20.1.1; '
            'hardware ethernet DE:AD:BE:EF:CA:F1; }',
        )
        # other order
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(data_centers=[self.dc2, self.dc1]),
        )
        self.assertEqual(
            config,
            'host sample1.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
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
            generate_dhcp_config_entries(),
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
            generate_dhcp_config_entries(),
        )
        self.assertEqual(
            config,
            'host name-from-ip.dc1 { fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }',
        )

    def test_multiple_domain_occurrence_entry(self):
        DHCPEntry.objects.create(ip='127.0.0.1', mac='deadbeefcafe')
        DHCPEntry.objects.create(ip='127.0.0.2', mac='deadbeefcaff')
        device = Device.objects.create(sn='sn123')
        Ethernet.objects.create(
            mac='deadbeefcafe', label="eth0", device=device,
        )
        Ethernet.objects.create(
            mac='deadbeefcaff', label="eth1", device=device,
        )
        IPAddress.objects.create(
            address='127.0.0.1',
            hostname='sample-hostname-1.dc1',
            device=device,
        )
        ip2 = IPAddress.objects.create(
            address='127.0.0.2',
            hostname='sample-hostname-1.dc1',
            device=device,
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(),
        )
        self.assertEqual(
            config,
            'host sample-hostname-1.dc1 '
            '{ fixed-address 127.0.0.1; hardware ethernet DE:AD:BE:EF:CA:FE; }'
        )
        ip2.hostname = 'sample-hostname-2.dc1'
        ip2.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config_entries(),
        )
        self.assertEqual(
            config,
            'host sample-hostname-1.dc1 '
            '{ fixed-address 127.0.0.1; '
            'hardware ethernet DE:AD:BE:EF:CA:FE; }\n'
            'host sample-hostname-2.dc1 '
            '{ fixed-address 127.0.0.2; hardware ethernet DE:AD:BE:EF:CA:FF; }'
        )

    def test_networks_configs(self):
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(),
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
            generate_dhcp_config_networks(),
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

    def test_env_networks_configs(self):
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(environments=[self.env2]),
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
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(environments=[self.env1, self.env2]),
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

    def test_dc_networks_configs(self):
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(data_centers=[self.dc1]),
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
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(data_centers=[self.dc2]),
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
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(
                data_centers=[self.dc1, self.dc2]
            ),
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
        # other order
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(
                data_centers=[self.dc2, self.dc1]
            ),
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

    def test_no_domain_networks_configs(self):
        self.env2.domain = None
        self.env2.save()
        config = _sanitize_dhcp_config(
            generate_dhcp_config_networks(),
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

    def test_dhcp_server_config(self):
        dhcp_server = DHCPServer.objects.create(
            ip='127.0.1.1',
            dhcp_config='SAMPLE DHCP CONFIG',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(dhcp_server=dhcp_server),
        )
        self.assertEqual(
            config,
            "SAMPLE DHCP CONFIG",
        )

    def test_dhcp_server_empty_config(self):
        dhcp_server = DHCPServer.objects.create(
            ip='127.0.1.2',
        )
        config = _sanitize_dhcp_config(
            generate_dhcp_config_head(dhcp_server=dhcp_server),
        )
        self.assertEqual(
            config,
            "",
        )
