# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status

from ralph.accounts.tests.factories import RegionFactory
from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser
from ralph.licences.tests.factories import LicenceFactory


class LicenceAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.licence1, self.licence2 = LicenceFactory.create_batch(2)
        region_pl = RegionFactory(name="pl")
        self.licence3 = LicenceFactory(region=region_pl)
        self.base_object = BackOfficeAssetFactory()
        self.base_object2 = BackOfficeAssetFactory(region=region_pl)
        LicenceUser.objects.create(licence=self.licence1, user=self.user1)
        BaseObjectLicence.objects.create(
            licence=self.licence2, base_object=self.base_object
        )
        self.service_env = ServiceEnvironmentFactory()
        self.licence4 = LicenceFactory(service_env=self.service_env)

    def test_get_licence_list(self):
        url = reverse("licence-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], Licence.objects.count())

    def test_get_licence_with_user_details(self):
        url = reverse("licence-detail", args=(self.licence1.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["number_bought"], self.licence1.number_bought)
        self.assertEqual(response.data["region"]["id"], self.licence1.region.id)
        self.assertEqual(
            response.data["manufacturer"]["id"], self.licence1.manufacturer.id
        )
        self.assertEqual(
            response.data["licence_type"]["id"], self.licence1.licence_type.id
        )
        self.assertEqual(response.data["software"]["id"], self.licence1.software.id)
        self.assertEqual(
            response.data["users"][0]["user"]["id"],
            self.user1.id,
        )
        self.assertEqual(
            response.data["depreciation_rate"], self.licence1.depreciation_rate
        )

    def test_get_licence_with_service_env(self):
        url = reverse("licence-detail", args=(self.licence4.id,))
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["service_env"]["id"], self.service_env.id)
        self.assertEqual(
            response.data["service_env"]["service"], self.service_env.service.name
        )
        self.assertEqual(
            response.data["service_env"]["environment"],
            self.service_env.environment.name,
        )

    def test_get_licence_with_base_object_details(self):
        url = reverse("licence-detail", args=(self.licence2.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["base_objects"][0]["base_object"].endswith(
                reverse("baseobject-detail", args=(self.base_object.id,))
            )
        )

    def test_api_region_validate_error(self):
        url = reverse("baseobjectlicence-list")
        data = {"base_object": self.base_object.id, "licence": self.licence1.id}
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"],
            ["Asset region is in a different region than licence."],
        )

    def test_api_region_validate_ok(self):
        url = reverse("baseobjectlicence-list")
        data = {"base_object": self.base_object2.id, "licence": self.licence3.id}
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            BaseObjectLicence.objects.filter(
                base_object=self.base_object2.id, licence=self.licence3.id
            ).exists()
        )
