from django.test import TestCase

from .factories import DNSServerGroupOrderFactory


class DNSServerGroupOrderTestCase(TestCase):
    def test_dns_server_group_order_should_return_dns_server_ip_as_str(self):
        """__str__ from DNSServerGroupOrder is crucial for DHCP"""
        server_group_order = DNSServerGroupOrderFactory()
        self.assertEqual(
            str(server_group_order.dns_server.ip_address), str(server_group_order)
        )
