# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import EthernetFactory
from ralph.networks.models import Network
from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


class IPAddressAPITests(RalphAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.net = NetworkFactory(address="127.0.0.0/24")
        cls.eth = EthernetFactory()

    def setUp(self):
        super().setUp()
        self.ip1 = IPAddressFactory(address="127.0.0.1")
        self.ip1.ethernet.refresh_from_db()  # to update mac
        self.ip_with_dhcp = IPAddressFactory(address="127.0.0.2", dhcp_expose=True)

    def test_get_ip_list_filter_by_dhcp_expose(self):
        url = "{}?{}".format(reverse("ipaddress-list"), "dhcp_expose=True")
        # TODO: 1 and true should also work
        # see https://github.com/tomchristie/django-rest-framework/issues/2122
        # for details
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_get_ip_list_filter_by_mac(self):
        url = "{}?ethernet__mac={}".format(
            reverse("ipaddress-list"), self.ip1.ethernet.mac
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_get_ip_list_filter_by_invalid_mac_400(self):
        url = "{}?ethernet__mac={}".format(reverse("ipaddress-list"), "(none)")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_ip_details(self):
        url = reverse("ipaddress-detail", args=(self.ip1.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ethernet"]["mac"], self.ip1.ethernet.mac)
        self.assertEqual(
            response.data["ethernet"]["ipaddress"]["address"], self.ip1.address
        )
        self.assertEqual(
            response.data["ethernet"]["base_object"]["id"],
            self.ip1.ethernet.base_object.id,
        )

    def test_change_network_should_not_pass(self):
        net = NetworkFactory(address="192.168.1.0/24")
        data = {"network": net.id}
        url = reverse("ipaddress-detail", args=(self.ip1.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ip1.refresh_from_db()
        self.assertEqual(self.ip1.network, self.net)

    def test_put_ip(self):
        data = {
            "address": "127.1.0.1",
            "hostname": "another-hostname",
            "is_management": True,
            "is_gateway": True,
            "ethernet": self.eth.id,
            "dhcp_expose": True,
        }
        url = reverse("ipaddress-detail", args=(self.ip1.id,))
        response = self.client.put(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ip1.refresh_from_db()
        self.assertEqual(self.ip1.address, "127.1.0.1")
        self.assertEqual(self.ip1.hostname, "another-hostname")
        self.assertTrue(self.ip1.is_management)
        self.assertTrue(self.ip1.dhcp_expose)
        self.assertTrue(self.ip1.is_gateway)
        self.assertEqual(self.ip1.ethernet, self.eth)

    def test_change_ip_address_already_occupied_should_not_pass(self):
        data = {"address": "127.0.0.2"}
        url = reverse("ipaddress-detail", args=(self.ip1.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "IP address with this IP address already exists.", response.data["address"]
        )

    def test_change_ip_address_with_dhcp_exposition_should_not_pass(self):
        data = {"address": "127.0.0.3"}
        url = reverse("ipaddress-detail", args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot change address when exposing in DHCP", response.data["__all__"]
        )

    def test_change_ip_hostname_with_dhcp_exposition_should_not_pass(self):
        data = {"hostname": "some-hostname"}
        url = reverse("ipaddress-detail", args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot change hostname when exposing in DHCP", response.data["__all__"]
        )

    def test_change_ip_ethernet_with_dhcp_exposition_should_not_pass(self):
        data = {"ethernet": self.eth.id}
        url = reverse("ipaddress-detail", args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot change ethernet when exposing in DHCP", response.data["__all__"]
        )

    def test_change_ip_dhcp_expose_with_dhcp_exposition_should_not_pass(self):
        data = {"dhcp_expose": False}
        url = reverse("ipaddress-detail", args=(self.ip_with_dhcp.id,))
        response = self.client.patch(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot remove entry from DHCP. Use transition to do this.",
            response.data["dhcp_expose"],
        )

    def test_delete_when_exposing_in_dhcp_should_not_pass(self):
        url = reverse("ipaddress-detail", args=(self.ip_with_dhcp.id,))
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Could not delete IPAddress when it is exposed in DHCP", response.data
        )


class NetworkAPITests(RalphAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.net1 = NetworkFactory(address="127.0.0.0/24")
        cls.net2 = NetworkFactory(address="128.0.0.0/24")

    def test_get_ip_list_filter_by_mac(self):
        url = "{}?address={}".format(reverse("network-list"), self.net1.address)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        network = response.data["results"][0]
        self.assertIsNotNone(network["min_ip"])
        self.assertIsNotNone(network["max_ip"])

    def test_create_network_sets_min_and_max_ip_and_ignores_passed_value(self):
        data = {
            "name": "test1",
            "address": "1.0.0.0/16",
            "min_ip": 222,
            "max_ip": 111,
        }

        url = reverse("network-list")
        response = self.client.post(url, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        network = Network.objects.get(pk=response.data["id"])

        # min and max ip are automatically assigned
        self.assertEqual(network.min_ip, 16777216)  # 1.0.0.0
        self.assertEqual(network.max_ip, 16842751)  # 1.0.255.255
