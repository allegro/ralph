# -*- coding: utf-8 -*-
from django.test import TestCase
from django.urls import reverse
from moneyed import PLN

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import BaseObjectLicence, Licence
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests.mixins import ClientMixin


class BaseObjectLicenceTest(ClientMixin, TestCase):
    def setUp(self):  # noqa
        super().setUp()
        self.login_as_user()
        region_pl = RegionFactory(name="pl")
        region_de = RegionFactory(name="de")
        self.licence = LicenceFactory(region=region_pl)
        self.bo_1 = BackOfficeAssetFactory(region=region_pl)
        self.bo_2 = BackOfficeAssetFactory(region=region_de)

    def test_create_new_licence(self):
        service_env = ServiceEnvironmentFactory()
        data = {
            "licence_type": self.licence.licence_type.id,
            "software": self.licence.software.id,
            "niw": "111",
            "region": self.licence.region.id,
            "price_0": 100,
            "price_1": "PLN",
            "number_bought": 3,
            "service_env": service_env.id,
            "custom_fields-customfieldvalue-content_type-object_id-TOTAL_FORMS": 3,
            "custom_fields-customfieldvalue-content_type-object_id-INITIAL_FORMS": 0,
            "custom_fields-customfieldvalue-content_type-object_id-MIN_NUM_FORMS": 0,
            "custom_fields-customfieldvalue-content_type-object_id-MAX_NUM_FORMS": 1000,
        }

        response = self.client.post(
            reverse("admin:licences_licence_add"), data=data, follow=True
        )
        new_licence = Licence.objects.get(niw="111")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("errors", response.context_data)
        self.assertEqual(new_licence.licence_type, self.licence.licence_type)
        self.assertEqual(new_licence.software, self.licence.software)
        self.assertEqual(new_licence.region, self.licence.region)
        self.assertEqual(new_licence.price.amount, 100)
        self.assertEqual(new_licence.price.currency, PLN)
        self.assertEqual(new_licence.number_bought, 3)
        self.assertEqual(new_licence.service_env, service_env)

    def test_add_base_object_licence_ok(self):
        data = {
            "baseobjectlicence_set-TOTAL_FORMS": 1,
            "baseobjectlicence_set-INITIAL_FORMS": 0,
            "baseobjectlicence_set-MIN_NUM_FORMS": 0,
            "baseobjectlicence_set-MAX_NUM_FORMS": 1000,
            "baseobjectlicence_set-0-id": "",
            "baseobjectlicence_set-0-licence": self.licence.id,
            "baseobjectlicence_set-0-base_object": self.bo_1.id,
            "baseobjectlicence_set-0-quantity": 1,
        }
        response = self.client.post(
            reverse("admin:licences_licence_assignments", args=(self.licence.id,)),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        base_object_licence = BaseObjectLicence.objects.filter(
            licence=self.licence, base_object=self.bo_1
        ).exists()
        self.assertTrue(base_object_licence)

    def test_add_base_object_licence_error(self):
        data = {
            "baseobjectlicence_set-TOTAL_FORMS": 1,
            "baseobjectlicence_set-INITIAL_FORMS": 0,
            "baseobjectlicence_set-MIN_NUM_FORMS": 0,
            "baseobjectlicence_set-MAX_NUM_FORMS": 1000,
            "baseobjectlicence_set-0-id": "",
            "baseobjectlicence_set-0-licence": self.licence.id,
            "baseobjectlicence_set-0-base_object": self.bo_2.id,
            "baseobjectlicence_set-0-quantity": 1,
        }
        response = self.client.post(
            reverse("admin:licences_licence_assignments", args=(self.licence.id,)),
            data=data,
            follow=True,
        )
        self.assertContains(
            response, "Asset region is in a different region than licence."
        )
