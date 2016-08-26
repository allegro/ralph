# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.networks.tests.factories import IPAddressFactory
from ralph.security.models import Risk, ScanStatus, SecurityScan, Vulnerability
from ralph.security.tests.factories import (
    SecurityScanFactory,
    VulnerabilityFactory
)


class SecurityScanAPITests(RalphAPITestCase):

    def setUp(self):
        super().setUp()
        self.security_scan = SecurityScanFactory()

    def test_get_security_scan_list(self):
        url = reverse('securityscan-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], SecurityScan.objects.count()
        )

    def test_get_security_scan_details(self):
        url = reverse('securityscan-detail', args=(self.security_scan.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in ['last_scan_date', 'next_scan_date']:
            self.assertEqual(
                response.data[field],
                getattr(self.security_scan, field).isoformat(),
            )
        for field in ['details_url', 'rescan_url']:
            self.assertEqual(
                response.data[field], getattr(self.security_scan, field)
            )
        self.assertEqual(response.data['scan_status'], ScanStatus.ok.name)
        self.assertEqual(
            response.data['base_object'],
            'http://testserver/api/base-objects/{}/'.format(
                self.security_scan.base_object.id
            )
        )
        self.assertEqual(
            len(response.data['vulnerabilities']),
            self.security_scan.vulnerabilities.count(),
        )
        self.assertEqual(
            response.data['vulnerabilities'][0]['id'],
            self.security_scan.vulnerabilities.all()[0].id,
        )

    def test_create_security_scan(self):
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability = VulnerabilityFactory()
        data = {
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': ScanStatus.ok.name,
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host_ip': ip.address,
            'vulnerabilities': [vulnerability.id, ],
        }

        url = reverse('securityscan-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        security_scan = SecurityScan.objects.get(pk=response.data['id'])
        self.assertEqual(
            security_scan.last_scan_date.isoformat(), data['last_scan_date']
        )
        self.assertEqual(security_scan.scan_status, ScanStatus.ok)
        self.assertEqual(
            security_scan.next_scan_date.isoformat(), data['next_scan_date']
        )
        self.assertEqual(security_scan.details_url, data['details_url'])
        self.assertEqual(security_scan.rescan_url, data['rescan_url'])
        self.assertEqual(security_scan.base_object, ip.base_object)
        self.assertEqual(security_scan.vulnerabilities.count(), 1)
        self.assertEqual(security_scan.vulnerabilities.get(), vulnerability)

    def test_patch_security_scan(self):
        ip = IPAddressFactory(address="192.168.128.66")
        url = reverse('securityscan-detail', args=(self.security_scan.id,))
        vulnerability = VulnerabilityFactory()
        data = {
            'last_scan_date': (
                datetime.now() + timedelta(days=10)
            ).isoformat(),
            'scan_status': ScanStatus.error.name,
            'next_scan_date': (
                datetime.now() + timedelta(days=15)
            ).isoformat(),
            'details_url': self.security_scan.details_url + '-new',
            'rescan_url': self.security_scan.rescan_url + '-new',
            'host_ip': ip.address,
            'vulnerabilities': [vulnerability.id, ],
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.security_scan.refresh_from_db()
        self.assertEqual(
            self.security_scan.last_scan_date.isoformat(),
            data['last_scan_date']
        )
        self.assertEqual(self.security_scan.scan_status, ScanStatus.error)
        self.assertEqual(
            self.security_scan.next_scan_date.isoformat(),
            data['next_scan_date']
        )
        self.assertEqual(self.security_scan.details_url, data['details_url'])
        self.assertEqual(self.security_scan.rescan_url, data['rescan_url'])
        self.assertEqual(self.security_scan.base_object, ip.base_object)
        self.assertEqual(self.security_scan.vulnerabilities.count(), 1)
        self.assertEqual(
            self.security_scan.vulnerabilities.get(), vulnerability,
        )


class VulnerabilityAPITests(RalphAPITestCase):

    def setUp(self):
        super().setUp()
        self.vulnerability = VulnerabilityFactory()

    def test_get_vulnerability_list(self):
        url = reverse('vulnerability-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], Vulnerability.objects.count()
        )

    def test_get_vulnerability_details(self):
        url = reverse('vulnerability-detail', args=(self.vulnerability.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['name'], self.vulnerability.name)
        self.assertEqual(
            response.data['patch_deadline'],
            self.vulnerability.patch_deadline.isoformat(),
        )
        self.assertEqual(response.data['risk'], Risk.low.name)
        self.assertEqual(
            response.data['external_vulnerability_id'],
            self.vulnerability.external_vulnerability_id,
        )

    def test_create_vulnerability(self):
        url = reverse('vulnerability-list')
        data = {
            'name': "vulnerability name",
            'patch_deadline': (
                datetime.now() + timedelta(days=10)
            ).isoformat(),
            'risk': Risk.low.name,
            'external_vulnerability_id': 100,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vulnerability = Vulnerability.objects.get(pk=response.data['id'])
        self.assertEqual(vulnerability.name, data['name'])
        self.assertEqual(
            vulnerability.patch_deadline.isoformat(), data['patch_deadline'],
        )
        self.assertEqual(vulnerability.risk, Risk.low)
        self.assertEqual(
            vulnerability.external_vulnerability_id,
            data['external_vulnerability_id']
        )

    def test_patch_vulnerability(self):
        url = reverse('vulnerability-detail', args=(self.vulnerability.id,))
        data = {
            'name': self.vulnerability.name + ' new',
            'patch_deadline': (
                self.vulnerability.patch_deadline + timedelta(days=3)
            ).isoformat(),
            'risk': Risk.high.name,
            'external_vulnerability_id': self.vulnerability.external_vulnerability_id + 10  # noqa
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.vulnerability.refresh_from_db()
        self.assertEqual(self.vulnerability.name, data['name'])
        self.assertEqual(
            self.vulnerability.patch_deadline.isoformat(),
            data['patch_deadline'])
        self.assertEqual(self.vulnerability.risk, Risk.high)
        self.assertEqual(
            self.vulnerability.external_vulnerability_id,
            data['external_vulnerability_id'])


class TestExternalVulnerability(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        ip = IPAddressFactory(address="192.168.128.10")
        self.vulnerability = VulnerabilityFactory()
        self.data = {
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': ScanStatus.ok.name,
            'next_scan_date': '2016-01-01T00:00:00',
            'host_ip': ip.address,
            'external_vulnerabilities': [
                self.vulnerability.external_vulnerability_id
            ],
        }

    def test_create_scan_by_external_id_works(self):
        response = self.client.post(
            reverse('securityscan-list'), self.data, format='json'
        )
        security_scan = SecurityScan.objects.get(pk=response.data['id'])
        self.assertEqual(
            self.vulnerability.id, security_scan.vulnerabilities.get().id
        )

    def test_create_scan_raise_error_when_both_vulnerabilities_empty(self):
        self.data['external_vulnerabilities'] = []
        response = self.client.post(
            reverse('securityscan-list'), self.data, format='json'
        )
        self.assertEqual(
            response.data,
            {'vulnerabilities': ['This list may not be empty.']},
        )
