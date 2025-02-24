from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


class NetworkAdminTestCase(TestCase):
    def setUp(self):
        self.network = NetworkFactory(address="10.20.30.0/24")
        self.ip1 = IPAddressFactory(address="10.20.30.40")
        self.ip2 = IPAddressFactory(address="10.20.30.41")
        self.ip_other = IPAddressFactory(address="10.30.30.40")

        self.user = get_user_model().objects.create_superuser(
            username="root", password="password", email="email@email.pl"
        )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)
        self.factory = RequestFactory()

    def test_admin_view_should_show_addresses_in_network(self):
        response = self.client.get(self.network.get_absolute_url())
        self.assertContains(response, "10.20.30.40")
        self.assertContains(response, "10.20.30.41")
        self.assertNotContains(response, "10.30.30.40")
