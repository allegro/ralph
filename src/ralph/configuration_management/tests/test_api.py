from datetime import datetime

from django.core.urlresolvers import reverse

from ralph.api.tests._base import RalphAPITestCase
from ralph.configuration_management.models import SCMScan, SCMScanStatus
from ralph.configuration_management.tests.factories import SCMScanFactory
from ralph.virtual.tests.factories import VirtualServerFullFactory


class TestSCMScanAPI(RalphAPITestCase):

    def test_post_by_hostname_creates_scm_scan_record(self):
        v_server = VirtualServerFullFactory()

        url = reverse(
            'scm-scan-post',
            kwargs={'hostname': v_server.hostname}
        )

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.ok.id
        }

        resp = self.client.post(url, data=data)

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(
            resp.data.get('base_object'),
            v_server.baseobject_ptr_id
        )
        self.assertEqual(resp.data.get('scan_status'), SCMScanStatus.ok.name)
        self.assertEqual(
            resp.data.get('last_scan_date'),
            data['last_scan_date']
        )

    def test_post_by_hostname_updates_scm_scan_record(self):
        v_server = VirtualServerFullFactory()
        existing_scan = SCMScanFactory(
            base_object=v_server.baseobject_ptr,
            scan_status=SCMScanStatus.ok
        )

        url = reverse(
            'scm-scan-post',
            kwargs={'hostname': v_server.hostname}
        )

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.fail.id
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)

        updated_scan = SCMScan.objects.get(pk=existing_scan.pk)
        self.assertEqual(updated_scan.scan_status, SCMScanStatus.fail)

        self.assertEqual(
            resp.data.get('base_object'),
            existing_scan.base_object_id
        )
        self.assertEqual(resp.data.get('scan_status'), SCMScanStatus.fail.name)
        self.assertEqual(
            resp.data.get('last_scan_date'),
            data['last_scan_date']
        )

    def test_double_post_does_not_create_duplicate_scm_scan_record(self):
        v_server = VirtualServerFullFactory()

        url = reverse(
            'scm-scan-post',
            kwargs={'hostname': v_server.hostname}
        )

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.fail.id
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 201)

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.fail.id
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            len(SCMScan.objects.all()), 1
        )

    def test_post_wrong_hostname_returns_404(self):
        url = reverse(
            'scm-scan-post',
            kwargs={'hostname': 'deadbeef.local'}
        )

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.fail.id
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 404)

    def test_creating_scm_scan_record_ignores_baseobject_id_in_data(self):
        v_server_1 = VirtualServerFullFactory()
        v_server_2 = VirtualServerFullFactory()

        url = reverse(
            'scm-scan-post',
            kwargs={'hostname': v_server_1.hostname}
        )

        data = {
            'last_scan_date': datetime.now().isoformat(),
            'scan_status': SCMScanStatus.fail.id,
            'base_object': v_server_2.baseobject_ptr_id
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(
            resp.data.get('base_object'),
            v_server_1.baseobject_ptr_id
        )
