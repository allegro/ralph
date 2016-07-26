from ipaddress import ip_address, ip_network

from ddt import data, ddt, unpack
from django.core.exceptions import ValidationError

from ralph.assets.models import AssetLastHostname
from ralph.assets.tests.factories import EthernetFactory
from ralph.networks.models.choices import IPAddressStatus
from ralph.networks.models.networks import IPAddress, Network
from ralph.networks.tests.factories import (
    IPAddressFactory,
    NetworkEnvironmentFactory
)
from ralph.tests import RalphTestCase


@ddt
class SimpleNetworkTest(RalphTestCase):
    def setUp(self):
        self.net1 = Network.objects.create(
            name='net1',
            address='192.168.0.0/16',
        )
        self.net2 = Network.objects.create(
            parent=self.net1,
            name='net2',
            address='192.168.0.0/17',
        )
        self.net3 = Network.objects.create(
            parent=self.net2,
            name='net3',
            address='192.168.128.0/17',
        )
        self.net4 = Network.objects.create(
            parent=self.net3,
            name='net4',
            address='192.168.133.0/24',
        )
        self.net5 = Network.objects.create(
            name='net5',
            address='192.169.133.0/24',
        )

        self.ip1 = IPAddress(address='192.168.128.10')
        self.ip1.save()
        self.ip2 = IPAddress(address='192.168.133.10')
        self.ip2.save()
        self.ip3 = IPAddress(address='192.168.128.11')
        self.ip3.save()

    @unpack
    @data(
        ('net1', 16),
        ('net2', 17),
    )
    def test_get_netmask(self, net, netmask):
        self.assertEquals(getattr(self, net).netmask, netmask)

    @unpack
    @data(
        ('net1', ['net2', 'net3', 'net4']),
        ('net3', ['net4']),
    )
    def test_get_subnetworks(self, net, correct):
        net_obj = getattr(self, net)
        res = Network.objects.get(pk=net_obj.pk).get_subnetworks()
        self.assertEquals(
            list(res), list(Network.objects.filter(name__in=correct))
        )


@ddt
class NetworkTest(RalphTestCase):
    @unpack
    @data(
        ('92.143.123.123', True),
        ('10.168.123.123', False),
    )
    def test_ip_is_public_or_no(self, ip, is_public):
        new_ip_address = IPAddress(address=ip)
        new_ip_address.save()
        self.assertEquals(new_ip_address.is_public, is_public)

    @unpack
    @data(
        ('::/128',),
        ('::1/128',),
        ('::/96',),
        ('::ffff:0:0/64',),
        ('2001:7f8::/32',),
        ('2001:db8::/32',),
        ('2002::/24',),
        ('3ffe::/16',),
        ('fd00::/7',),
        ('fe80::/10',),
        ('fec0::/10',),
        ('ff00::/8',),
    )
    def test_network_should_support_ipv6(self, net):
        network = Network(
            name='ipv6 ready',
            address=net,
        )
        self.assertEqual(network.network, ip_network(net, strict=False))

    @unpack
    @data(
        ('192.168.100.0/24', '192.168.100.1', True),
        ('10.1.1.0/24', '10.1.1.1', True),
        ('10.1.1.0/24', '10.1.1.2', True),
        ('10.1.1.0/31', '10.1.1.2', False),
        ('10.1.1.0/31', '10.1.1.1', True),
        ('10.1.1.0/31', '10.1.1.0', True),
    )
    def test_ip_address_should_return_network(self, network, ip, should_return):
        net = Network.objects.create(
            name='ip_address_should_return_network',
            address=network,
        )
        ip = IPAddress.objects.create(address=ip)
        result = ip.get_network()
        if should_return:
            self.assertEqual(net, result)
        else:
            self.assertEqual(None, result)

    @unpack
    @data(
        ('10.1.1.0/24', '10.1.0.255'),
        ('10.1.1.0/24', '10.1.2.0'),
    )
    def test_ip_address_should_not_return_network(self, network, ip):
        Network.objects.create(
            name='ip_address_should_return_network',
            address=network,
        )
        ip = IPAddress.objects.create(address=ip, network=None)
        result = ip.get_network()
        self.assertEqual(None, result)

    def test_reserve_margin_addresses_should_reserve_free_addresses(self):
        net = Network.objects.create(
            name='ip_address_should_return_network',
            address='10.1.1.0/24',
        )
        ip1 = IPAddress.objects.create(address='10.1.1.1')
        ip2 = IPAddress.objects.create(address='10.1.1.254')
        result = net.reserve_margin_addresses(bottom_count=10, top_count=10)
        self.assertEqual(18, net.ips.filter(status=IPAddressStatus.reserved).count())  # noqa
        self.assertEqual(18, result[0])
        self.assertEqual(set([ip1.number, ip2.number]), result[1])

    def test_create_ip_address(self):
        Network.objects.create(
            name='test_create_ip_address',
            address='10.1.1.0/24',
        )
        IPAddress.objects.create(address='10.1.1.0')

    @unpack
    @data(
        ('192.168.1.0/24', 254),
        ('192.168.1.0/30', 2),
        ('192.168.1.0/31', 2),
    )
    def test_net_size(self, addr, size):
        net = Network.objects.create(address=addr)
        self.assertEqual(net.size, size)

    @unpack
    @data(
        ('192.168.1.0/29', ip_address('192.168.1.1'), []),
        ('192.168.1.0/31', ip_address('192.168.1.0'), []),
        ('192.168.1.0/31', ip_address('192.168.1.1'), ['192.168.1.0']),
        ('192.168.1.0/31', None, ['192.168.1.0', '192.168.1.1']),
    )
    def test_get_first_free_ip(self, network_addr, first_free, used):
        net = Network.objects.create(address=network_addr)
        ips = []
        for ip in used:
            IPAddress.objects.create(address=ip, network=net)
        if ips:
            IPAddress.object.bulk_create(ips)
        self.assertEqual(net.get_first_free_ip(), first_free)

    def test_sub_network_should_assign_automatically(self):
        net = Network.objects.create(
            name='net', address='192.168.5.0/24'
        )
        subnet = Network.objects.create(
            name='subnet', address='192.168.5.0/25'
        )
        self.assertEqual(net, subnet.parent)

    def test_sub_network_should_change_automatically(self):
        net1 = Network.objects.create(
            name='net', address='10.20.30.0/24'
        )
        net2 = Network.objects.create(
            name='net2', address='10.20.30.240/28'
        )

        self.assertEqual(net1, net2.parent)

        net3 = Network.objects.create(
            name='net3', address='10.20.30.128/25'
        )

        self.refresh_objects_from_db(net2, net3)
        self.assertEqual(net2.parent, net3)
        self.assertIn(net2, net3.get_immediate_subnetworks())
        self.assertEqual(net3.parent, net1)

        net4 = Network.objects.create(
            name='net4', address='10.20.40.128/28'
        )
        net5 = Network.objects.create(
            name='net5', address='10.20.40.0/24'
        )
        net3.address = '10.20.40.128/25'
        net3.save()

        self.refresh_objects_from_db(net1, net2, net3, net4, net5)

        self.assertEqual(net3.parent, net5)
        self.assertEqual(net4.parent, net3)
        self.assertEqual(net2.parent, net1)

        net3.delete()
        self.refresh_objects_from_db(net4, net5)
        self.assertEqual(net4.parent, net5)

    def test_sub_network_should_reassign_ip(self):
        ip = IPAddress.objects.create(address='192.169.58.1')
        self.assertEqual(ip.network, None)
        net = Network.objects.create(
            name='net', address='192.169.58.0/24'
        )
        sub1 = Network.objects.create(
            name='sub_net1', address='192.169.58.0/25'
        )
        sub2 = Network.objects.create(
            name='sub_net2', address='192.169.58.128/26'
        )
        self.refresh_objects_from_db(net)
        net.save()
        self.refresh_objects_from_db(ip, sub1, sub2)
        self.assertEqual(ip.network, sub1)

    def test_delete_network_shouldnt_delete_related_ip(self):
        net = Network.objects.create(
            name='net', address='192.169.58.0/24'
        )
        ip = IPAddress.objects.create(address='192.169.58.1', network=net)
        net.delete()
        ip.refresh_from_db()
        self.assertTrue(ip)

    def test_reserved_count(self):
        net = Network.objects.create(
            name='net', address='192.169.58.0/24'
        )
        self.assertEqual(net.reserved_bottom, 0)
        self.assertEqual(net.reserved_top, 0)

        # add one reserved IP
        ip11 = IPAddress.objects.create(
            address='192.169.58.1', status=IPAddressStatus.reserved
        )
        self.assertEqual(net.reserved_bottom, 1)
        ip21 = IPAddress.objects.create(
            address='192.169.58.254', status=IPAddressStatus.reserved
        )
        self.assertEqual(net.reserved_top, 1)

        # add another reserved IP on both sides
        ip12 = IPAddress.objects.create(
            address='192.169.58.2', status=IPAddressStatus.reserved
        )
        self.assertEqual(net.reserved_bottom, 2)
        ip22 = IPAddress.objects.create(
            address='192.169.58.253', status=IPAddressStatus.reserved
        )
        self.assertEqual(net.reserved_top, 2)

        # add more reserved IPs inside network
        IPAddress.objects.create(
            address='192.169.58.3', status=IPAddressStatus.reserved
        )
        IPAddress.objects.create(
            address='192.169.58.252', status=IPAddressStatus.reserved
        )
        IPAddress.objects.create(
            address='192.169.58.10', status=IPAddressStatus.reserved
        )
        IPAddress.objects.create(
            address='192.169.58.240', status=IPAddressStatus.reserved
        )
        self.assertEqual(net.reserved_bottom, 3)
        self.assertEqual(net.reserved_top, 3)

        # delete reversed IPs
        ip12.delete()
        ip22.delete()
        self.assertEqual(net.reserved_bottom, 1)
        self.assertEqual(net.reserved_top, 1)

        ip11.delete()
        ip21.delete()
        self.assertEqual(net.reserved_bottom, 0)
        self.assertEqual(net.reserved_top, 0)


class NetworkEnvironmentTest(RalphTestCase):
    def test_issue_next_hostname(self):
        ne = NetworkEnvironmentFactory(
            hostname_template_prefix='s123',
            hostname_template_postfix='.dc.local',
            hostname_template_counter_length=5,
        )
        ne2 = NetworkEnvironmentFactory(
            # same params as ne
            hostname_template_prefix='s123',
            hostname_template_postfix='.dc.local',
            hostname_template_counter_length=5,
        )
        ne3 = NetworkEnvironmentFactory(
            # other params comparing to ne
            hostname_template_prefix='s1',
            hostname_template_postfix='.dc.local',
            hostname_template_counter_length=5,
        )
        self.assertEqual(ne.issue_next_free_hostname(), 's12300001.dc.local')
        self.assertEqual(ne.issue_next_free_hostname(), 's12300002.dc.local')
        self.assertEqual(ne.issue_next_free_hostname(), 's12300003.dc.local')
        self.assertEqual(ne2.issue_next_free_hostname(), 's12300004.dc.local')
        self.assertEqual(ne.issue_next_free_hostname(), 's12300005.dc.local')
        self.assertEqual(ne3.issue_next_free_hostname(), 's100001.dc.local')

    def test_issue_next_hostname_overflow(self):
        alhg = AssetLastHostname.objects.create(
            prefix='s123',
            postfix='.dc.local',
            counter=99998,
        )
        ne = NetworkEnvironmentFactory(
            hostname_template_prefix='s123',
            hostname_template_postfix='.dc.local',
            hostname_template_counter_length=5,
        )
        self.assertEqual(ne.issue_next_free_hostname(), 's12399999.dc.local')
        self.assertEqual(ne.issue_next_free_hostname(), 's123100000.dc.local')

    def test_get_next_hostname(self):
        ne = NetworkEnvironmentFactory(
            hostname_template_prefix='s123',
            hostname_template_postfix='.dc.local',
            hostname_template_counter_length=5,
        )
        # check if hostname is not increased
        self.assertEqual(ne.next_free_hostname, 's12300001.dc.local')
        self.assertEqual(ne.next_free_hostname, 's12300001.dc.local')


class IPAddressTest(RalphTestCase):
    def setUp(self):
        self.ip = IPAddressFactory()

    def test_delete_ethernet_should_delete_related_ip(self):
        ip = IPAddressFactory()
        ip.ethernet.delete()
        with self.assertRaises(IPAddress.DoesNotExist):
            ip.refresh_from_db()

    def test_delete_ip_should_not_delete_ethernet(self):
        ip = IPAddressFactory()
        eth = ip.ethernet
        ip.delete()
        eth.refresh_from_db()

    def test_clear_hostname_should_pass(self):
        self.ip.hostname = None
        self.ip.clean()
        self.ip.save()

    def test_clear_hostname_with_dhcp_exposition_should_not_pass(self):
        self.ip.dhcp_expose = True
        self.ip.save()
        self.ip.hostname = None
        with self.assertRaises(
            ValidationError,
            msg='Cannot expose in DHCP without hostname'
        ):
            self.ip.clean()

    def test_clear_mac_address_without_dhcp_exposition_should_pass(self):
        self.ip.ethernet.mac = None
        self.ip.ethernet.save()
        self.ip.clean()
        self.ip.save()

    def test_clear_mac_address_with_ip_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip.ethernet.mac = None
        self.ip.ethernet.save()
        self.ip.dhcp_expose = True
        with self.assertRaises(
            ValidationError,
            msg='Cannot expose in DHCP without MAC address'
        ):
            self.ip.clean()

    def test_detach_ethernet_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip.ethernet = None
        self.ip.save()
        self.ip.dhcp_expose = True
        with self.assertRaises(
            ValidationError,
            msg='Cannot expose in DHCP without MAC address'
        ):
            self.ip.clean()

    def test_change_hostname_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip.dhcp_expose = True
        self.ip.save()
        self.ip.hostname = 'another-hostname'
        with self.assertRaises(
            ValidationError,
            msg='Cannot change hostname when exposing in DHCP'
        ):
            self.ip.clean()

    def test_change_address_with_dhcp_exposition_should_not_pass(self):  # noqa
        self.ip.dhcp_expose = True
        self.ip.save()
        self.ip.address = '127.0.0.2'
        with self.assertRaises(
            ValidationError,
            msg='Cannot change address when exposing in DHCP'
        ):
            self.ip.clean()

    def test_change_ethernet_with_dhcp_exposition_should_not_pass(self):  # noqa
        eth = EthernetFactory()
        self.ip.dhcp_expose = True
        self.ip.save()
        self.ip.ethernet = eth
        with self.assertRaises(
            ValidationError,
            msg='Cannot change ethernet when exposing in DHCP'
        ):
            self.ip.clean()
