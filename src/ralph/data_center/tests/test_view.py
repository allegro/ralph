from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.core.urlresolvers import reverse
from django.test import TestCase

from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFullFactory
)
from ralph.security.models import ScanStatus
from ralph.security.tests.factories import (
    SecurityScanFactory,
    VulnerabilityFactory
)
from ralph.tests.mixins import ClientMixin
from ralph.virtual.tests.factories import (
    CloudHostFullFactory,
    VirtualServerFullFactory
)


def tomorrow():
    return datetime.now() + timedelta(days=1)


def yesterday():
    return datetime.now() + timedelta(days=-1)


class DataCenterAssetViewTest(ClientMixin, TestCase):
    def test_changelist_view(self):
        self.login_as_user()
        DataCenterAssetFullFactory.create_batch(10)
        with self.assertNumQueries(18):
            self.client.get(
                reverse('admin:data_center_datacenterasset_changelist'),
            )


class DCHostViewTest(ClientMixin, TestCase):
    def setUp(self):
        self.login_as_user()

    def test_changelist_view(self):
        DataCenterAssetFullFactory.create_batch(5)
        VirtualServerFullFactory.create_batch(5)
        CloudHostFullFactory.create_batch(4)
        ClusterFactory.create_batch(4)
        with self.assertNumQueries(19):
            result = self.client.get(
                reverse('admin:data_center_dchost_changelist'),
            )
        # DCAssets - 5
        # VirtualServer + hypervisors - 10
        # Cluster - 4
        # CloudHost + hypervisors - 8
        self.assertEqual(result.context_data['cl'].result_count, 27)

    def test_changelist_datacenterasset_location(self):
        DataCenterAssetFullFactory(
            rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1')

    def test_changelist_virtualserver_location(self):
        VirtualServerFullFactory(
            parent=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
                hostname='s12345.mydc.net',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1 / s12345.mydc.net')

    def test_changelist_cloudhost_location(self):
        CloudHostFullFactory(
            hypervisor=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
                hostname='s12345.mydc.net',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1 / s12345.mydc.net')

    def test_changelist_cluster_location(self):
        cluster = ClusterFactory()
        cluster.baseobjectcluster_set.create(
            is_master=True,
            base_object=DataCenterAssetFullFactory(
                rack__name='Rack #1',
                rack__server_room__name='SR1',
                rack__server_room__data_center__name='DC1',
            )
        )
        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, 'DC1 / SR1 / Rack #1')


class DCHostScanStatusInListingTest(ClientMixin, TestCase):

    def setUp(self):
        self.login_as_user()
        self.asset = DataCenterAssetFullFactory(
            rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )

    def test_listing_show_ok_when_scan_succeed_and_no_vulnerabilities(
        self
    ):
        SecurityScanFactory(
            base_object=self.asset.baseobject_ptr, vulnerabilities=[],
        )

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, "Host clean")

    def test_listing_show_ok_when_scan_succeed_and_vulnerability_before_deadline(
        self
    ):
        SecurityScanFactory(
            base_object=self.asset.baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline=tomorrow())
            ],
        )

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )

        self.assertContains(result, "Host clean")

    def test_listing_show_fail_when_scan_succeed_and_got_exceeded_vulnerability(self):
        scan = SecurityScanFactory(
            base_object=self.asset.baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline=yesterday())
            ],
        )
        self.assertTrue(scan.vulnerabilities.exists())

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, "Got vulnerabilities: 1")

    def test_listing_show_correct_vuls_count_when_scan_has_different_vuls(self):
        scan = SecurityScanFactory(
            base_object=self.asset.baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline=tomorrow()),
                VulnerabilityFactory(patch_deadline=yesterday()),
            ],
        )
        self.assertTrue(scan.vulnerabilities.exists())

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, "Got vulnerabilities: 1")

    def test_listing_show_failed_when_scan_failed(self):
        SecurityScanFactory(
            base_object=self.asset.baseobject_ptr,
            scan_status=ScanStatus.fail.id,
            vulnerabilities=[],
        )

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, "Scan failed")

    def test_listing_show_failed_icon_when_scan_error(self):
        SecurityScanFactory(
            base_object=self.asset.baseobject_ptr,
            scan_status=ScanStatus.error.id,
            vulnerabilities=[],
        )

        result = self.client.get(
            reverse('admin:data_center_dchost_changelist'),
        )
        self.assertContains(result, "Scan failed")


class DCHostFilterByPatchDeadline(ClientMixin, TestCase):
    def setUp(self):
        self.login_as_user()
        self.asset_no_vuls = DataCenterAssetFullFactory(
            rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )
        self.scan_no_vuls = SecurityScanFactory(
            base_object=self.asset_no_vuls.baseobject_ptr, vulnerabilities=[],
        )

        self.today = datetime.now()
        self.yesterday = self.today + timedelta(days=-1)
        self.tomorrow = self.today + timedelta(days=1)

        self.asset_with_today_vul = DataCenterAssetFullFactory(
            rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )
        self.scan_with_vuls2 = SecurityScanFactory(
            base_object=self.asset_with_today_vul.baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(
                    patch_deadline=self.today,
                )
            ]
        )

        self.asset_vuls2 = DataCenterAssetFullFactory(
           rack__name='Rack #1',
            rack__server_room__name='SR1',
            rack__server_room__data_center__name='DC1',
        )
        self.scan_with_vuls2 = SecurityScanFactory(
            base_object=self.asset_vuls2.baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(
                    patch_deadline=self.today + timedelta(days=30)
                )
            ]
        )

    def test_patch_deadline_filters_hosts(self):
        FORMAT = '%Y-%m-%d'
        url = (
            '?'.join([
                reverse('admin:data_center_dchost_changelist',),
                urlencode({
                    'securityscan__vulnerabilities__patch_deadline__start': self.yesterday.strftime(FORMAT),  # noqa
                    'securityscan__vulnerabilities__patch_deadline__end': self.tomorrow.strftime(FORMAT),  # noqa
                })
            ])
        )

        response = self.client.get(url, follow=True)

        self.assertEqual(
            int(response.context_data['object_id']),
            self.asset_with_today_vul.id,
        )
