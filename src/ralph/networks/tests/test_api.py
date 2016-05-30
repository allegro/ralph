# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import EthernetFactory
from ralph.networks.models import IPAddressStatus
from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


class IPAddressAPITests(RalphAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.net = NetworkFactory(address='127.0.0.0/24')
        cls.eth = EthernetFactory()

    def setUp(self):
        super().setUp()
        self.ip1 = IPAddressFactory(address='127.0.0.1')
        self.ip_with_dhcp = IPAddressFactory(
            address='127.0.0.2', dhcp_expose=True
        )

    def test_get_ip_list_filter_by_dhcp_expose(self):
        url = '{}?{}'.format(reverse('ipaddress-list'), 'dhcp_expose=True')
        # TODO: 1 and true should also work
        # see https://github.com/tomchristie/django-rest-framework/issues/2122
        # for details
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_change_network_should_not_pass(self):
        net = NetworkFactory(address='192.168.1.0/24')
        data = {'network': net.id}
        url = reverse('ipaddress-detail', args=(self.ip1.id,))
        response = self.client.patch(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ip1.refresh_from_db()
        self.assertEqual(self.ip1.network, self.net)

    def test_put_ip(self):
        data = {
            'address': '127.1.0.1',
            'hostname': 'another-hostname',
            'is_management': True,
            'is_gateway': True,
            'status': 'reserved',
            'ethernet': self.eth.id,
            'dhcp_expose': True,
        }
        url = reverse('ipaddress-detail', args=(self.ip1.id,))
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ip1.refresh_from_db()
        self.assertEqual(self.ip1.address, '127.1.0.1')
        self.assertEqual(self.ip1.hostname, 'another-hostname')
        self.assertTrue(self.ip1.is_management)
        self.assertTrue(self.ip1.dhcp_expose)
        self.assertTrue(self.ip1.is_gateway)
        self.assertEqual(self.ip1.ethernet, self.eth)
        self.assertEqual(self.ip1.status, IPAddressStatus.reserved)

    def test_change_ip_address_already_occupied_should_not_pass(self):
        data = {'address': '127.0.0.2'}
        url = reverse('ipaddress-detail', args=(self.ip1.id,))
        response = self.client.patch(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This field must be unique.', response.data['address'])

    def test_change_ip_address_with_dhcp_exposition_should_not_pass(self):
        data = {'address': '127.0.0.3'}
        url = reverse('ipaddress-detail', args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_ip_hostname_with_dhcp_exposition_should_not_pass(self):
        data = {'hostname': 'some-hostname'}
        url = reverse('ipaddress-detail', args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_ip_ethernet_with_dhcp_exposition_should_not_pass(self):
        data = {'ethernet': self.eth.id}
        url = reverse('ipaddress-detail', args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
