# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from rest_framework import status

# from ralph.accounts.models import Region
from ralph.api.tests._base import RalphAPITestCase
from ralph.data_center.tests.factories import IPAddressFactory
from ralph.security.choices import Risk, ScanStatus
from ralph.security.models import SecurityScan, Vulnerability
from ralph.security.tests.factories import (
    SecurityScanFactory, VulnerabilityFactory,
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
            response.data['asset'],
            'http://testserver/api/base-objects/{}/'.format(
                self.security_scan.asset.id
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
        # region = Region.objects.create(name='EU')
        ip = IPAddressFactory(address="192.168.128.10")
        vulnerability = VulnerabilityFactory()
        data = {
            'last_scan_date': '2015-01-01T00:00:00',
            'scan_status': ScanStatus.ok.name,
            'next_scan_date': '2016-01-01T00:00:00',
            'details_url': 'https://example.com/scan-deatils',
            'rescan_url': 'https://example.com/rescan-url',
            'host ip': ip.address,
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
        self.assertEqual(security_scan.asset, ip.asset)
        self.assertEqual(security_scan.asset, ip.asset)
        self.assertEqual(
            security_scan.vulnerabilities.count(), 1
        )
        self.assertEqual(
            security_scan.vulnerabilities.get(), vulnerability
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

# class SupportAPITests(RalphAPITestCase):
#    def setUp(self):
#        super().setUp()
#        self.support = SupportFactory(name='support1')
#
#    def test_create_support(self):
#        region = Region.objects.create(name='EU')
#        url = reverse('support-list')
#        data = {
#            'name': 'support2',
#            'region': region.id,
#            'contract_id': '12345',
#            'status': 'new',
#            'date_to': '2020-01-01',
#        }
#        response = self.client.post(url, data, format='json')
#        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#        support = Support.objects.get(pk=response.data['id'])
#        self.assertEqual(support.name, 'support2')
#        self.assertEqual(support.region, region)
#        self.assertEqual(support.contract_id, '12345')
#        self.assertEqual(support.status, SupportStatus.new.id)
#        self.assertEqual(support.date_to, date(2020, 1, 1))
#
#    def test_patch_support(self):
#        url = reverse('support-detail', args=(self.support.id,))
#        data = {
#            'name': 'support2',
#            'contract_id': '12345',
#            'date_to': '2015-12-31',
#        }
#        response = self.client.patch(url, data, format='json')
#        self.assertEqual(response.status_code, status.HTTP_200_OK)
#        self.support.refresh_from_db()
#        self.assertEqual(self.support.name, 'support2')
#        self.assertEqual(self.support.contract_id, '12345')
#        self.assertEqual(self.support.date_to, date(2015, 12, 31))
