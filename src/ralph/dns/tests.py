# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import TestCase

from ralph.dns.forms import RecordType
from ralph.dns.views import get_dns_records


class TestGetDnsRecords(TestCase):

    @patch('ralph.dns.views.get_api_result')
    def test_return_empty_when_api_returns_empty(self, mocked):
        mocked.return_value = []
        found_dns = get_dns_records(['192.168.0.1'])
        self.assertEqual(found_dns, [])

    @patch('ralph.dns.views.get_api_result')
    def test_return_dns_records_when_api_returns_records(self, mocked):
        data = {
            'content': '127.0.0.3',
            'name': '1.test.pl',
            'type': 'A',
            'id': 1
        }
        mocked.return_value = [data]
        found_dns = get_dns_records(['192.168.0.1'])
        self.assertEqual(len(found_dns), 1)
        self.assertEqual(found_dns[0]['content'], data['content'])
        self.assertEqual(found_dns[0]['name'], data['name'])
        self.assertEqual(found_dns[0]['type'], RecordType.a)
