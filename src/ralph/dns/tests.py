# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import override_settings, TestCase

from ralph.dns.dnsaas import DNSaaS
from ralph.dns.forms import RecordType
from ralph.dns.views import DNSaaSIntegrationNotEnabledError, DNSView


class TestGetDnsRecords(TestCase):

    def setUp(self):
        self.dnsaas = DNSaaS()

    @patch.object(DNSaaS, 'get_api_result')
    def test_return_empty_when_api_returns_empty(self, mocked):
        mocked.return_value = []
        found_dns = self.dnsaas.get_dns_records(['192.168.0.1'])
        self.assertEqual(found_dns, [])

    @patch.object(DNSaaS, 'get_api_result')
    def test_return_dns_records_when_api_returns_records(self, mocked):
        data = {
            'content': '127.0.0.3',
            'name': '1.test.pl',
            'type': 'A',
            'id': 1
        }
        mocked.return_value = [data]
        found_dns = self.dnsaas.get_dns_records(['192.168.0.1'])
        self.assertEqual(len(found_dns), 1)
        self.assertEqual(found_dns[0]['content'], data['content'])
        self.assertEqual(found_dns[0]['name'], data['name'])
        self.assertEqual(found_dns[0]['type'], RecordType.a)

    @override_settings(DNSAAS_URL='http://dnsaas.com/')
    def test_build_url(self):
        self.assertEqual(
            self.dnsaas.build_url('domains'),
            'http://dnsaas.com/api/v2/domains/'
        )

    @override_settings(DNSAAS_URL='http://dnsaas.com/')
    def test_build_url_with_version(self):
        self.assertEqual(
            self.dnsaas.build_url('domains', version='v1'),
            'http://dnsaas.com/api/v1/domains/'
        )

    @override_settings(DNSAAS_URL='http://dnsaas.com/')
    def test_build_url_with_id(self):
        self.assertEqual(
            self.dnsaas.build_url('domains', id=1),
            'http://dnsaas.com/api/v2/domains/1/'
        )

    @override_settings(DNSAAS_URL='http://dnsaas.com/')
    def test_build_url_with_get_params(self):
        self.assertEqual(
            self.dnsaas.build_url('domains', get_params=[('name', 'ralph')]),
            'http://dnsaas.com/api/v2/domains/?name=ralph'
        )

    @override_settings(DNSAAS_URL='http://dnsaas.com/')
    def test_build_url_with_id_and_get_params(self):
        self.assertEqual(
            self.dnsaas.build_url(
                'domains', id=1, get_params=[('name', 'ralph')]
            ),
            'http://dnsaas.com/api/v2/domains/1/?name=ralph'
        )


class TestDNSView(TestCase):
    @override_settings(ENABLE_DNSAAS_INTEGRATION=False)
    def test_dnsaasintegration_disabled(self):
        with self.assertRaises(DNSaaSIntegrationNotEnabledError):
            DNSView()

    @override_settings(ENABLE_DNSAAS_INTEGRATION=True)
    def test_dnsaasintegration_enabled(self):
        # should not raise exception
        DNSView()


from ralph.data_center.models.virtual import BaseObjectCluster
from ralph.data_center.tests.factories import RackFactory
from ralph.data_center.tests.factories import ClusterFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.virtual.tests.factories import VirtualServerFactory
from ralph.dns.publishers import _publish_data_to_dnsaaas
class TestPublisher(TestCase):

    def setUp(self):
        self.dc_asset = DataCenterAssetFactory(
            rack=RackFactory(), position=1, slot_no='1',
        )
        self.virtual_server = VirtualServerFactory(
            parent=DataCenterAssetFactory(
                rack=RackFactory(), position=1, slot_no='1',
            )
        )

        # TODO:: factory handling that
        self.cluster = ClusterFactory()
        self.cluster_1 = ClusterFactory()
        self.boc_1 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=DataCenterAssetFactory()
        )
        self.boc_2 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=DataCenterAssetFactory(),
            is_master=True
        )
        import ipdb
        ipdb.set_trace()

    def test_dc_asset_gets_data_ok(self):
        data = _publish_data_to_dnsaaas(self.dc_asset)
        self.assertEqual(data, [{
            'content': 'www',
            'name': 'ralph0.allegro.pl',
            'owner': 'ralph',
            'purpose': 'VENTURE'
        }, {
            'content': 'ralph',
            'name': 'ralph0.allegro.pl',
            'owner': 'ralph',
            'purpose': 'ROLE',
        }, {
            'content': 'DL360',
            'name': 'ralph0.allegro.pl',
            'owner': 'ralph',
            'purpose': 'MODEL'
        }, {
            'content': 'DC1 / Server Room A / Rack #100 / 1 / 1',
            'name': 'ralph0.allegro.pl',
            'owner': 'ralph',
            'purpose': 'LOCATION'
        }])

    def test_cluster_gets_data_ok(self):
        data = _publish_data_to_dnsaaas(self.cluster)
        self.assertEqual(data, [{
        }])

    def test_virtual_server_gets_data_ok(self):
        data = _publish_data_to_dnsaaas(self.virtual_server)
        self.assertEqual(data, [{
            'content': 'worker',
            'name': 's000.local',
            'owner': 'ralph',
            'purpose': 'VENTURE'
        }, {
            'content': 'auth',
            'name': 's000.local',
            'owner': 'ralph',
            'purpose': 'ROLE'
        }, {
            'content': 'DL380p',
            'name': 's000.local',
            'owner': 'ralph',
            'purpose': 'MODEL'
        }, {
            'content': 'DC2 / Server Room B / Rack #101 / 1 / 1',
            'name': 's000.local',
            'owner': 'ralph',
            'purpose': 'LOCATION'
        }])
