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
