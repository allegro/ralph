# -*- coding: utf-8 -*-
from django.http.request import QueryDict
from rest_framework import serializers

from ralph.api.tests._base import RalphAPITestCase
from ralph.data_center.tests.factories import IPAddressFactory
from ralph.security.api import SaveSecurityScanSerializer
from ralph.security.tests.factories import (
    SecurityScanFactory,
    VulnerabilityFactory
)


class SaveSecurityScanSerializerTests(RalphAPITestCase):

    def setUp(self):
        super().setUp()
        self.security_scan = SecurityScanFactory()

    def _dict2QueryDict(self, data_dict):
        qdict = QueryDict('', mutable=True)
        qdict.update(data_dict)
        return qdict

    def test_external_id_is_converted_to_local(self):
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability_1 = VulnerabilityFactory()
        vulnerability_2 = VulnerabilityFactory()
        data = self._dict2QueryDict({
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': 'ok',
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host_ip': ip.address,
            'vulnerabilities': vulnerability_1.id,
            'external_vulnerabilities': vulnerability_2.external_vulnerability_id,  # noqa
        })
        scan_serializer = SaveSecurityScanSerializer(
            context={'request': None})
        deserialized = scan_serializer.to_internal_value(data)

        self.assertEqual(
            deserialized['vulnerabilities'],
            [vulnerability_1, vulnerability_2],
        )

    def test_error_raised_when_unknown_external_id(self):
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability = VulnerabilityFactory()
        data = self._dict2QueryDict({
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': 'ok',
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host_ip': ip.address,
            'vulnerabilities': vulnerability.id,
            'external_vulnerabilities': '12345678',
        })
        scan_serializer = SaveSecurityScanSerializer(
            context={'request': None})
        with self.assertRaises(serializers.ValidationError):
            scan_serializer.to_internal_value(data)
