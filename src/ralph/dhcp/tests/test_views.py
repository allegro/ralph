from ddt import data, ddt, unpack
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import http_date

from ralph.assets.tests.factories import EthernetFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.dhcp.models import DHCPEntry
from ralph.dhcp.views import DHCPEntriesView
from ralph.networks.models.networks import Network
from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


@ddt
class DHCPConfigTest(TestCase):
    def test_config_endpoint_should_return_200(self):
        get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.client.login(username='test', password='test')
        network = NetworkFactory(address='192.168.1.0/24')
        url = '{}?env={}'.format(
            reverse('dhcp_config_entries'), network.network_environment
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_config_endpoint_should_return_401_when_user_is_anonymous(self):
        network = NetworkFactory(address='192.168.1.0/24')
        url = '{}?env={}'.format(
            reverse('dhcp_config_entries'), network.network_environment
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_config_endpoint_should_return_304(self):
        network = NetworkFactory(address='192.168.1.0/24')
        url = '{}?env={}'.format(
            reverse('dhcp_config_entries'), network.network_environment
        )
        response = self.client.get(
            url, HTTP_IF_MODIFIED_SINCE=http_date(network.modified.timestamp())
        )
        self.assertEqual(response.status_code, 304)

    @unpack
    @data(
        ('dc=foo&env=bar', 'Only DC or ENV mode available.'),
        ('', 'Please specify DC or ENV.'),
    )
    def test_view_should_return_400(self, params, message):
        url = '{}?{}'.format(
            reverse('dhcp_config_entries'), params
        )
        response = self.client.get(url)
        self.assertContains(response, message, status_code=400)


class DHCPEntriesViewTest(TestCase):
    def setUp(self):
        self.view = DHCPEntriesView()

    def test_get_last_modified_should_return_ip_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        ip = IPAddressFactory(address='192.168.1.2')
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(
            returned.strftime("%Y-%m-%d %H:%M:%S"),
            ip.modified.strftime("%Y-%m-%d %H:%M:%S")
        )

    def test_get_last_modified_should_return_network_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        ip = IPAddressFactory(address='192.168.1.2')
        network.save()
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(
            returned.strftime("%Y-%m-%d %H:%M:%S"),
            network.modified.strftime("%Y-%m-%d %H:%M:%S")
        )

    def test_get_last_modified_should_return_ethernet_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        ethernet = EthernetFactory()
        ip = IPAddressFactory(address='192.168.1.2', ethernet=ethernet)
        ethernet.save()
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(
            returned.strftime("%Y-%m-%d %H:%M:%S"),
            ethernet.modified.strftime("%Y-%m-%d %H:%M:%S")
        )

    def test_get_last_modified_should_return_assets_ethernet_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        asset = DataCenterAssetFactory()
        ethernet = EthernetFactory(base_object=asset)
        ethernet.save()
        ip = IPAddressFactory(
            address='192.168.1.2', base_object=asset, ethernet=ethernet
        )
        ethernet.save()
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(
            returned.strftime("%Y-%m-%d %H:%M:%S"),
            ethernet.modified.strftime("%Y-%m-%d %H:%M:%S")
        )

    def test_get_last_modified_should_run_5_queries(self):
        network = NetworkFactory(address='192.168.1.0/24')
        with self.assertNumQueries(5):
            self.view.get_last_modified(
                Network.objects.filter(id__in=[network.id])
            )

    def test_filter_duplicated_hostnames(self):
        network = NetworkFactory(address='192.168.1.0/24')
        asset = DataCenterAssetFactory()
        ethernet = EthernetFactory(base_object=asset)
        ethernet.save()
        IPAddressFactory(
            hostname='host1.mydc.net', address='192.168.1.2', ethernet=ethernet,
            dhcp_expose=True
        )
        ethernet2 = EthernetFactory()
        ethernet2.save()
        IPAddressFactory(
            hostname='host1.mydc.net', address='192.168.1.3',
            ethernet=ethernet2, dhcp_expose=True
        )
        ethernet3 = EthernetFactory()
        ethernet3.save()
        ip = IPAddressFactory(
            hostname='host2.mydc.net', address='192.168.1.4',
            ethernet=ethernet3, dhcp_expose=True
        )
        entries = self.view._get_dhcp_entries(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(DHCPEntry.objects.count(), 3)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].pk, ip.pk)
