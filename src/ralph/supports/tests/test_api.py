# -*- coding: utf-8 -*-
from datetime import date

from django.urls import reverse
from rest_framework import status

from ralph.accounts.models import Region
from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.supports.models import Support, SupportStatus
from ralph.supports.tests.factories import (
    BackOfficeAssetSupportFactory,
    DataCenterAssetSupportFactory,
    SupportFactory,
)


class SupportAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.service_env = ServiceEnvironmentFactory()
        self.support = SupportFactory(name="support1", service_env=self.service_env)

    def test_get_supports_list(self):
        url = reverse("support-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], Support.objects.count())

    def test_get_support_details(self):
        url = reverse("support-detail", args=(self.support.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.support.name)
        self.assertEqual(response.data["contract_id"], self.support.contract_id)
        self.assertEqual(response.data["status"], "new")
        self.assertEqual(response.data["support_type"]["id"], self.support.support_type.id)
        self.assertEqual(response.data["service_env"]["service"], self.service_env.service.name)
        self.assertEqual(
            response.data["service_env"]["environment"],
            self.service_env.environment.name,
        )
        # TODO: baseobjects

    def test_create_support(self):
        region = Region.objects.create(name="EU")
        url = reverse("support-list")
        data = {
            "name": "support2",
            "region": region.id,
            "contract_id": "12345",
            "status": "new",
            "date_to": "2020-01-01",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        support = Support.objects.get(pk=response.data["id"])
        self.assertEqual(support.name, "support2")
        self.assertEqual(support.region, region)
        self.assertEqual(support.contract_id, "12345")
        self.assertEqual(support.status, SupportStatus.new.id)
        self.assertEqual(support.date_to, date(2020, 1, 1))

    def test_patch_support(self):
        url = reverse("support-detail", args=(self.support.id,))
        data = {
            "name": "support2",
            "contract_id": "12345",
            "date_to": "2015-12-31",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.support.refresh_from_db()
        self.assertEqual(self.support.name, "support2")
        self.assertEqual(self.support.contract_id, "12345")
        self.assertEqual(self.support.date_to, date(2015, 12, 31))

    def test_support_with_include_assets(self):
        support1 = SupportFactory(name="support_with_assets_1")
        support2 = SupportFactory(name="support_with_assets_2")
        support3 = SupportFactory(name="support_with_assets_3")

        BackOfficeAssetSupportFactory.create_batch(3, support=support1)
        BackOfficeAssetSupportFactory.create_batch(2, support=support2)

        DataCenterAssetSupportFactory.create_batch(2, support=support1)
        DataCenterAssetSupportFactory.create_batch(3, support=support3)

        # Mix of both base_object types for one support
        BackOfficeAssetSupportFactory.create_batch(2, support=support3)

        support4 = SupportFactory(name="support_with_assets_4")
        BackOfficeAssetSupportFactory.create_batch(3, support=support4)
        DataCenterAssetSupportFactory.create_batch(3, support=support4)
        SupportFactory.create_batch(10)

        url = reverse("support-list")

        with self.assertQueriesMoreOrLess(7, plus_minus=2):
            response = self.client.get(url, {"include_assets": "true"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)  # 4 with assets + 10 without + 1 from setUp

        for result in response.data["results"]:
            if result["name"] == "support_with_assets_1":
                self.assertEqual(len(result["backoffice_assets"]), 3)
                self.assertEqual(len(result["datacenter_assets"]), 2)
                self.assertIn("model", result["backoffice_assets"][0])
                self.assertIn("manufacturer", result["backoffice_assets"][0])
                self.assertIn("service_env", result["backoffice_assets"][0])
            elif result["name"] == "support_with_assets_2":
                self.assertEqual(len(result["backoffice_assets"]), 2)
                self.assertEqual(len(result["datacenter_assets"]), 0)
            elif result["name"] == "support_with_assets_3":
                self.assertEqual(len(result["backoffice_assets"]), 2)
                self.assertEqual(len(result["datacenter_assets"]), 3)

    def test_support_without_include_assets_parameter(self):
        support = SupportFactory(name="support_minimal")
        BackOfficeAssetSupportFactory.create_batch(2, support=support)
        DataCenterAssetSupportFactory.create_batch(2, support=support)

        url = reverse("support-detail", args=(support.id,))
        with self.assertQueriesMoreOrLess(6, plus_minus=2):
            response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "support_minimal")

        self.assertIn("base_objects", response.data)
        self.assertEqual(len(response.data["base_objects"]), 4)

        self.assertNotIn("backoffice_assets", response.data)
        self.assertNotIn("datacenter_assets", response.data)
