from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from ralph.api.tests._base import RalphAPITestCase
from ralph.configuration_management.models import SCMCheckResult, SCMStatusCheck
from ralph.configuration_management.tests.factories import SCMStatusCheckFactory
from ralph.virtual.tests.factories import VirtualServerFullFactory


class TestSCMScanAPI(RalphAPITestCase):
    def test_post_by_hostname_creates_scm_status_record(self):
        v_server = VirtualServerFullFactory()

        url = reverse("scm-info-post", kwargs={"hostname": v_server.hostname})

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.scm_ok.id,
        }

        resp = self.client.post(url, data=data)

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data.get("base_object"), v_server.baseobject_ptr_id)
        self.assertEqual(resp.data.get("check_result"), SCMCheckResult.scm_ok.raw)
        self.assertEqual(resp.data.get("last_checked"), data["last_checked"])

    def test_delete_scm_status_record(self):
        v_server = VirtualServerFullFactory()
        existing_scan = SCMStatusCheckFactory(
            base_object=v_server.baseobject_ptr, check_result=SCMCheckResult.scm_ok
        )

        url = reverse("scm-info-post", kwargs={"hostname": v_server.hostname})

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        with self.assertRaises(ObjectDoesNotExist):
            SCMStatusCheck.objects.get(pk=existing_scan.pk)

    def test_delete_wrong_hostname_returns_404(self):
        url = reverse("scm-info-post", kwargs={"hostname": "deadbeef.local"})

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)

    def test_delete_non_existing_scm_status_record_returns_404(self):
        v_server = VirtualServerFullFactory()

        url = reverse("scm-info-post", kwargs={"hostname": v_server.hostname})

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)

    def test_post_by_hostname_updates_scm_status_record(self):
        v_server = VirtualServerFullFactory()
        existing_scan = SCMStatusCheckFactory(
            base_object=v_server.baseobject_ptr, check_result=SCMCheckResult.scm_ok
        )

        url = reverse("scm-info-post", kwargs={"hostname": v_server.hostname})

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.check_failed.id,
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)

        updated_scan = SCMStatusCheck.objects.get(pk=existing_scan.pk)
        self.assertEqual(updated_scan.check_result, SCMCheckResult.check_failed)
        self.assertFalse(updated_scan.ok)
        self.assertEqual(resp.data.get("base_object"), existing_scan.base_object_id)
        self.assertEqual(resp.data.get("check_result"), SCMCheckResult.check_failed.raw)
        self.assertEqual(resp.data.get("last_checked"), data["last_checked"])

    def test_double_post_does_not_create_duplicate_scm_status_record(self):
        v_server = VirtualServerFullFactory()

        url = reverse("scm-info-post", kwargs={"hostname": v_server.hostname})

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.check_failed.id,
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 201)

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.check_failed.id,
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(SCMStatusCheck.objects.all()), 1)

    def test_post_wrong_hostname_returns_404(self):
        url = reverse("scm-info-post", kwargs={"hostname": "deadbeef.local"})

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.check_failed.id,
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 404)

    def test_creating_scm_status_record_ignores_baseobject_id_in_data(self):
        v_server_1 = VirtualServerFullFactory()
        v_server_2 = VirtualServerFullFactory()

        url = reverse("scm-info-post", kwargs={"hostname": v_server_1.hostname})

        data = {
            "last_checked": datetime.now().isoformat(),
            "check_result": SCMCheckResult.check_failed.id,
            "base_object": v_server_2.baseobject_ptr_id,
        }

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(resp.data.get("base_object"), v_server_1.baseobject_ptr_id)
