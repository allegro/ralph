# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.urls import reverse

from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests import RalphTestCase
from ralph.tests.mixins import ClientMixin


class BaseObjectLicenceCleanTest(RalphTestCase):
    def setUp(self):
        super().setUp()
        self.region_pl = RegionFactory(name="pl")
        self.region_de = RegionFactory(name="de")
        self.licence_de = LicenceFactory(region=self.region_de)
        self.bo_asset = BackOfficeAssetFactory(region=self.region_pl)

    def test_region_validate(self):
        base_object_licence = BaseObjectLicence()
        base_object_licence.licence = self.licence_de
        base_object_licence.base_object = self.bo_asset
        with self.assertRaisesRegex(
            ValidationError, ("Asset region is in a different region than licence.")
        ):
            base_object_licence.clean()


class LicenceTest(RalphTestCase):
    def setUp(self):
        super().setUp()
        self.licence_1 = LicenceFactory(number_bought=3)
        self.licence_2 = LicenceFactory(number_bought=1)
        self.user_1 = UserFactory()
        self.bo_asset = BackOfficeAssetFactory()

    def test_get_autocomplete_queryset(self):
        with self.assertNumQueries(2):
            self.assertCountEqual(
                Licence.get_autocomplete_queryset().values_list("pk", flat=True),
                [self.licence_1.pk, self.licence_2.pk],
            )

    def test_get_autocomplete_queryset_all_used(self):
        BaseObjectLicence.objects.create(
            base_object=self.bo_asset,
            licence=self.licence_1,
            quantity=1,
        )
        LicenceUser.objects.create(user=self.user_1, licence=self.licence_1, quantity=2)
        with self.assertNumQueries(2):
            self.assertCountEqual(
                Licence.get_autocomplete_queryset().values_list("pk", flat=True),
                [self.licence_2.pk],
            )


class LicenceFormTest(TransitionTestCase, ClientMixin):
    def test_service_env_not_required(self):
        self.assertTrue(self.login_as_user())
        licence = LicenceFactory()

        url = reverse("admin:licences_licence_change", args=(licence.pk,))
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        form = resp.context["adminform"].form

        self.assertIn("service_env", form.fields)
        self.assertFalse(form.fields["service_env"].required)

    def test_depreciation_rate_not_required(self):
        self.assertTrue(self.login_as_user())
        licence = LicenceFactory()

        url = reverse("admin:licences_licence_change", args=(licence.pk,))
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        form = resp.context["adminform"].form

        self.assertIn("depreciation_rate", form.fields)
        self.assertFalse(form.fields["depreciation_rate"].required)
