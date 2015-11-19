# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework import status

# from ralph.accounts.models import Region
from ralph.api.tests._base import RalphAPITestCase
from ralph.data_center.tests.factories import IPAddressFactory
from ralph.security.choices import Risk, ScanStatus
from ralph.security.models import SecurityScan, Vulnerability
from ralph.security.tests.factories import (
    SecurityScanFactory, VulnerabilityFactory,
)
from ralph.security.api import SaveSecurityScanSerializer




class SaveSecurityScanSerializerTests(RalphAPITestCase):

    def setUp(self):
        super().setUp()
        self.security_scan = SecurityScanFactory()


    def test_external_id_is_converted_to_local(self):
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability_1 = VulnerabilityFactory()
        vulnerability_2 = VulnerabilityFactory()
        data = {
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': 'ok',
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host ip': ip.address,
            'vulnerabilities': [vulnerability_1.id],
            'external_vulnerabilities': [vulnerability_2.external_vulnerability_id],  # noqa
        }
        scan_serializer = SaveSecurityScanSerializer(context={'request': None})
        deserialized = scan_serializer.to_internal_value(data)

        self.assertEqual(
            deserialized['vulnerabilities'],
            [vulnerability_1, vulnerability_2],
        )

    def test_error_raised_when_unknown_external_id(self):
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability = VulnerabilityFactory()
        data = {
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': 'ok',
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host ip': ip.address,
            'vulnerabilities': [vulnerability.id],
            'external_vulnerabilities': ['12345678'],
        }
        scan_serializer = SaveSecurityScanSerializer(context={'request': None})
        with self.assertRaises(serializers.ValidationError):
            deserialized = scan_serializer.to_internal_value(data)
