from ddt import data, ddt, unpack
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import http_date

from ralph.assets.tests.factories import EthernetFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.dhcp.views import DHCPEntriesView
from ralph.networks.models.networks import Network
from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


@ddt
class DHCPConfigTest(TestCase):
    def test_config_endpoint_should_return_200(self):
        network = NetworkFactory(address='192.168.1.0/24')
        url = '{}?env={}'.format(
            reverse('dhcp_config_entries'), network.network_environment
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(returned, ip.modified)

    def test_get_last_modified_should_return_network_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        ip = IPAddressFactory(address='192.168.1.2')
        network.save()
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(returned, network.modified)

    def test_get_last_modified_should_return_ethernet_modified(self):
        network = NetworkFactory(address='192.168.1.0/24')
        ethernet = EthernetFactory()
        ip = IPAddressFactory(address='192.168.1.2', ethernet=ethernet)
        ethernet.save()
        returned = self.view.get_last_modified(
            Network.objects.filter(id__in=[network.id])
        )
        self.assertEqual(returned, ethernet.modified)

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
        self.assertEqual(returned, ethernet.modified)

    def test_get_last_modified_should_run_4_queries(self):
        network = NetworkFactory(address='192.168.1.0/24')
        with self.assertNumQueries(4):
            self.view.get_last_modified(
               Network.objects.filter(id__in=[network.id])
            )
