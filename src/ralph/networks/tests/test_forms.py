from django.contrib.auth import get_user_model
from django.test import RequestFactory

from ralph.assets.models.components import Ethernet
from ralph.data_center.tests.factories import DataCenterFactory
from ralph.networks.models import IPAddress
from ralph.networks.tests.factories import (
    IPAddressFactory,
    NetworkEnvironmentFactory,
    NetworkFactory
)
from ralph.tests import RalphTestCase
from ralph.tests.models import PolymorphicTestModel


class NetworkInlineTestCase(RalphTestCase):
    def setUp(self):
        self.inline_prefix = "ethernet_set-"
        self.obj1 = PolymorphicTestModel.objects.create(hostname="abc")
        self.obj2 = PolymorphicTestModel.objects.create(hostname="xyz")
        self.ip1 = IPAddressFactory(
            ethernet__base_object=self.obj1,
            address="127.0.0.1",
            is_management=True,
        )
        self.ip2 = IPAddressFactory(
            ethernet__base_object=self.obj2,
            address="127.1.0.1",
            is_management=True,
        )
        self.eth1 = self.ip1.ethernet
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.factory = RequestFactory()

    def _prepare_inline_data(self, d):
        return {"{}{}".format(self.inline_prefix, k): v for (k, v) in d.items()}

    def test_adding_new_record_should_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-address": "127.0.0.2",
            "1-mac": "10:20:30:40:50:60",
            "1-label": "eth1",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        ip = IPAddress.objects.get(address="127.0.0.2")
        self.assertEqual(ip.hostname, "def")
        self.assertFalse(ip.is_management)
        self.assertFalse(ip.dhcp_expose)
        self.assertEqual(ip.ethernet.mac, "10:20:30:40:50:60")
        self.assertEqual(ip.ethernet.label, "eth1")
        self.assertEqual(ip.ethernet.base_object.pk, self.obj1.pk)

    def test_adding_new_record_without_ip_and_hostname_should_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-mac": "10:20:30:40:50:60",
            "1-label": "eth1",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        eth = Ethernet.objects.get(mac="10:20:30:40:50:60")
        self.assertEqual(eth.label, "eth1")
        self.assertEqual(eth.base_object.pk, self.obj1.pk)
        # ip should not be created
        with self.assertRaises(IPAddress.DoesNotExist):
            eth.ipaddress

    def test_adding_new_record_without_mac_should_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-address": "127.0.0.2",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        ip = IPAddress.objects.get(address="127.0.0.2")
        self.assertEqual(ip.hostname, "def")
        self.assertFalse(ip.is_management)
        self.assertFalse(ip.dhcp_expose)
        self.assertFalse(bool(ip.ethernet.mac))  # mac is either None or ''
        self.assertFalse(bool(ip.ethernet.label))
        self.assertEqual(ip.ethernet.base_object.pk, self.obj1.pk)

    def test_adding_multiple_new_record_without_mac_should_pass(self):
        # test for storing mac as null
        inline_data = {
            "TOTAL_FORMS": 3,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-address": "127.0.0.2",
            "2-base_object": self.obj1.id,
            "2-hostname": "def",
            "2-address": "127.0.0.3",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)

    def test_adding_new_record_without_mac_and_ip_should_not_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-label": "eth1",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        for err in response.context_data["errors"]:
            self.assertIn("At least one of mac, address is required", err)

    def test_adding_new_record_with_existing_ip_should_not_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-mac": "11:12:13:14:15:16",
            "1-address": self.ip2.address,  # duplicated ip!
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Address {} already exist.".format(self.ip2.address)
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_more_than_one_ip_is_management(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-hostname": "def",
            "1-base_object": self.obj1.id,
            "1-address": "127.0.0.2",
            "1-mac": "",
            "1-label": "",
            "1-is_management": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Only one management IP address can be assigned to this asset",
            response.context_data["errors"],
        )

    def test_empty_address_and_not_empty_hostname_should_not_pass(self):
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-hostname": self.ip1.hostname,
            "0-address": self.ip1.address,
            "0-mac": self.eth1.mac,
            "0-label": "",
            "0-is_management": "on",
            "1-hostname": "def",
            "1-base_object": self.obj1.id,
            "1-address": "",
            "1-mac": "10:20:30:40:50:60",
            "1-label": "",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = (
            "Address is required when one of hostname, is_management, "
            "dhcp_expose is filled"
        )
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))


class NetworkInlineWithDHCPExposeTestCase(RalphTestCase):
    def setUp(self):
        self.inline_prefix = "ethernet_set-"
        self.obj1 = PolymorphicTestModel.objects.create(hostname="abc")
        self.ip1 = IPAddressFactory(
            ethernet__base_object=self.obj1,
            ethernet__mac="10:20:30:40:50:60",
            hostname="s11.dc.local",
            address="127.0.0.1",
            is_management=True,
        )
        self.eth1 = self.ip1.ethernet
        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.factory = RequestFactory()

    def _prepare_inline_data(self, d):
        return {"{}{}".format(self.inline_prefix, k): v for (k, v) in d.items()}

    def test_dhcp_expose_readonly_fields_should_not_change_their_value(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eth10",
            # readonly fields modification!
            "0-hostname": "s222.dc.local",
            "0-address": "127.1.1.1",
            "0-mac": "11:11:11:11:11:11",
            # notice missing dhcp_expose field
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        # besides 302, readonly fields are untouched
        self.ip1.refresh_from_db()
        self.assertEqual(self.ip1.address, "127.0.0.1")
        self.assertEqual(self.ip1.hostname, "s11.dc.local")
        self.assertEqual(self.ip1.dhcp_expose, True)
        self.eth1.refresh_from_db()
        self.assertEqual(self.eth1.mac, "10:20:30:40:50:60")
        # other fields could be changed
        self.assertEqual(self.eth1.label, "eth10")

    def test_dhcp_expose_delete_should_not_work(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eth10",
            "0-hostname": "s222.dc.local",
            "0-address": "127.1.1.1",
            "0-mac": "11:11:11:11:11:11",
            "0-DELETE": "on",  # deleting row with DHCP entry!
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot delete entry if its exposed in DHCP"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_for_new_record_should_pass(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eth10",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-address": "127.0.0.2",
            "1-mac": "10:10:10:10:10:10",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        ip = IPAddress.objects.get(address="127.0.0.2")
        self.assertEqual(ip.hostname, "def")
        self.assertTrue(ip.dhcp_expose)
        self.assertEqual(ip.ethernet.mac, "10:10:10:10:10:10")
        self.assertEqual(ip.ethernet.label, "eth10")
        self.assertEqual(ip.ethernet.base_object.pk, self.obj1.pk)

    def test_dhcp_expose_for_new_record_duplicate_hostname_should_not_pass(self):  # noqa
        network = NetworkFactory(
            address="127.0.0.0/24",
            network_environment=NetworkEnvironmentFactory(
                data_center=DataCenterFactory(name="DC1")
            ),
        )
        self.test_dhcp_expose_for_new_record_should_pass()  # generate duplicate
        obj2 = PolymorphicTestModel.objects.create(hostname="xyz")
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": obj2.id,
            "0-mac": "ff:ff:ff:ff:ff:ff",
            "0-label": "eth10",
            "1-base_object": obj2.id,
            "1-hostname": self.ip1.hostname,
            "1-address": "127.0.0.3",
            "1-mac": "11:11:11:11:11:11",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": obj2.hostname,
            "id": obj2.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(obj2.get_absolute_url(), data, follow=True)
        self.assertEqual(response.status_code, 200)
        msg = 'Hostname "{hostname}" is already exposed in DHCP in {dc}.'.format(  # noqa
            hostname=self.ip1.hostname, dc=network.network_environment.data_center
        )
        self.assertIn("errors", response.context_data)
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_for_existing_record_duplicate_hostname_should_not_pass(self):  # noqa
        network = NetworkFactory(
            address="192.168.0.0/24",
            network_environment=NetworkEnvironmentFactory(
                data_center=DataCenterFactory(name="DC1")
            ),
        )
        name = "some.hostname"
        IPAddressFactory(
            dhcp_expose=True, hostname=name, address="192.168.0.7"
        ).save()
        self.ip1.hostname = name
        self.ip1.address = "192.168.0.12"
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eth10",
            "1-base_object": self.obj1.id,
            "1-hostname": name,
            "1-address": "192.168.0.33",
            "1-mac": "10:10:10:10:10:10",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data, follow=True)
        msg = 'Hostname "{hostname}" is already exposed in DHCP in {dc}.'.format(  # noqa
            hostname=self.ip1.hostname, dc=network.network_environment.data_center
        )
        self.assertIn("errors", response.context_data)
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_for_existing_record_should_pass(self):
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eth10",
            "0-hostname": "s11.dc.local",
            "0-address": "127.0.0.1",
            "0-mac": "10:20:30:40:50:60",
            "0-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        ip = IPAddress.objects.get(address="127.0.0.1")
        self.assertEqual(ip.hostname, "s11.dc.local")
        self.assertTrue(ip.dhcp_expose)
        self.assertEqual(ip.ethernet.mac, "10:20:30:40:50:60")
        self.assertEqual(ip.ethernet.label, "eth10")
        self.assertEqual(ip.ethernet.base_object.pk, self.obj1.pk)

    def test_dhcp_expose_without_address_for_new_record_should_not_pass(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "1-base_object": self.obj1.id,
            "1-hostname": "",
            "1-address": "",
            "1-mac": "10:10:10:10:10:10",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without IP address"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_with_address_exist_for_new_record_should_not_pass(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "1-base_object": self.obj1.id,
            "1-hostname": "",
            "1-address": self.ip1.address,
            "1-mac": "10:10:10:10:10:10",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        error_messages = [
            "Cannot expose in DHCP without IP address",
            "Address {} already exist.".format(self.ip1.address),
        ]
        for msg in error_messages:
            self.assertTrue(
                any([msg in err for err in response.context_data["errors"]])
            )

    def test_dhcp_expose_without_mac_for_new_record_should_not_pass(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "1-base_object": self.obj1.id,
            "1-hostname": "def",
            "1-address": "127.0.0.2",
            "1-mac": "",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without MAC address"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_without_hostname_for_new_record_should_not_pass(self):
        self.ip1.dhcp_expose = True
        self.ip1.save()
        inline_data = {
            "TOTAL_FORMS": 2,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "1-base_object": self.obj1.id,
            "1-hostname": "",
            "1-address": "127.0.0.2",
            "1-mac": "10:10:10:10:10:10",
            "1-label": "eth10",
            "1-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without hostname"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_without_address_for_existing_record_should_not_pass(self):  # noqa
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "0-hostname": "",
            "0-address": "",
            "0-mac": "10:10:10:10:10:10",
            "0-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without IP address"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_without_mac_for_existing_record_should_not_pass(self):
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "0-hostname": "def",
            "0-address": "127.0.0.2",
            "0-mac": "",
            "0-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without MAC address"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))

    def test_dhcp_expose_without_hostname_for_existing_record_should_not_pass(self):  # noqa
        inline_data = {
            "TOTAL_FORMS": 1,
            "INITIAL_FORMS": 1,
            "0-id": self.eth1.id,
            "0-base_object": self.obj1.id,
            "0-label": "eht10",
            "0-hostname": "",
            "0-address": "127.0.0.2",
            "0-mac": "10:10:10:10:10:10",
            "0-dhcp_expose": "on",
        }
        data = {
            "hostname": self.obj1.hostname,
            "id": self.obj1.id,
        }
        data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.obj1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        msg = "Cannot expose in DHCP without hostname"
        self.assertTrue(any([msg in err for err in response.context_data["errors"]]))
