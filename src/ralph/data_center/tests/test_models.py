from ralph.data_center.models.networks import (
    IPAddress,
    Network,
    get_network_tree
)
from ralph.tests import RalphTestCase


class NetworkTest(RalphTestCase):
    def setUp(self):
        self.net1 = Network.objects.create(
            name="test1",
            address="192.168.0.0/16",
        )
        self.net2 = Network.objects.create(
            name="test2",
            address="192.168.0.0/17",
        )
        self.net3 = Network.objects.create(
            name="test3",
            address="192.168.128.0/17",
            reserved=5,
            reserved_top_margin=5,
        )
        self.net4 = Network.objects.create(
            name="test4",
            address="192.168.133.0/24",
        )
        self.net5 = Network.objects.create(
            name="test5",
            address="192.169.133.0/24",
        )

        self.ip1 = IPAddress(address="192.168.128.10")
        self.ip1.save()
        self.ip2 = IPAddress(address="192.168.133.10")
        self.ip2.save()
        self.ip3 = IPAddress(address="192.168.128.11")
        self.ip3.save()

    def test_get_netmask(self):
        self.assertEquals(self.net1.get_netmask(), 16)
        self.assertEquals(self.net2.get_netmask(), 17)

    def test_get_subnetworks(self):
        res = self.net1.get_subnetworks()
        correct = [self.net2, self.net3, self.net4]
        self.assertEquals(res, correct)

        res = self.net3.get_subnetworks()
        correct = [self.net4]
        self.assertEquals(res, correct)

    def test_get_address_summary(self):
        ret = self.net3.get_total_ips()
        self.assertEquals(ret, 32767)
        ret = self.net3.get_free_ips()
        self.assertEquals(ret, 32500)
        ret = self.net3.get_ip_usage_range()
        correct_range = [self.ip1, self.ip3, self.net4]
        self.assertEquals(ret, correct_range)

    def test_get_ip_usage_aggregated(self):
        ret = self.net3.get_ip_usage_aggregated()
        correct = [
            {
                'amount': 10,
                'range_end': u'192.168.128.9',
                'range_start': u'192.168.128.0',
                'type': 'free',
            },
            {
                'amount': 2,
                'range_end': u'192.168.128.11',
                'range_start': u'192.168.128.10',
                'type': 'addr',
            },
            {
                'amount': 1268,
                'range_end': u'192.168.132.255',
                'range_start': u'192.168.128.12',
                'type': 'free',
            },
            {
                'amount': 257,
                'range_end': u'192.168.134.0',
                'range_start': u'192.168.133.0',
                'type': self.net4,
            },
            {
                'amount': 31232,
                'range_end': '192.169.0.0',
                'range_start': '192.168.134.1',
                'type': 'free',
            },
        ]
        self.assertEquals(ret, correct)

    def test_get_network_tree(self):
        res = get_network_tree()
        correct = [
            {
                'network': self.net1,
                'subnetworks': [
                    {
                        'network': self.net2,
                        'subnetworks': [],
                    },
                    {
                        'network': self.net3,
                        'subnetworks': [
                            {
                                'network': self.net4,
                                'subnetworks': [],
                            }
                        ]
                    },
                    {
                        'network': self.net4,
                        'subnetworks': [],
                    }
                ]
            },
            {
                'network': self.net5,
                'subnetworks': [],
            }
        ]
        self.assertEquals(res, correct)

    def test_ip_is_public_or_no(self):
        ip_list = [
            ('92.143.123.123', True),
            ('10.168.123.123', False),
        ]
        for ip, is_public in ip_list:
            new_ip_address = IPAddress(address=ip)
            new_ip_address.save()
            self.assertEquals(new_ip_address.is_public, is_public)
