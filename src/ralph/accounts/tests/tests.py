# -*- coding: utf-8 -*-
import unittest
from datetime import date

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from ralph.accounts.ldap import manager_country_attribute_populate
from ralph.accounts.management.commands.ldap_sync import (
    _truncate,
    ldap_module_exists
)
from ralph.accounts.models import RalphUser, Region
from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.back_office.tests.factories import (
    BackOfficeAssetFactory,
    WarehouseFactory
)
from ralph.licences.models import LicenceUser
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests import factories
from ralph.tests.mixins import ClientMixin

NO_LDAP_MODULE = not ldap_module_exists


@unittest.skipIf(NO_LDAP_MODULE, "'ldap' module is not installed")
class LdapSyncTest(TestCase):
    def test_long_surname_is_truncated(self):
        too_long_surname = "long-surname" * 50
        ldap_dict = {"sn": [too_long_surname]}
        default_django_surname_length = 150
        _truncate("sn", "last_name", ldap_dict)
        self.assertEqual(
            ldap_dict["sn"], [too_long_surname[:default_django_surname_length]]
        )

    def test_short_surname_stays_unmodified(self):
        short_surname = "short-surname"
        ldap_dict = {"sn": [short_surname]}
        _truncate("sn", "last_name", ldap_dict)
        self.assertEqual(ldap_dict["sn"], [short_surname])

    def test_truncate_works_when_no_sn(self):
        ldap_dict = {}
        _truncate("sn", "last_name", ldap_dict)


@unittest.skipIf(NO_LDAP_MODULE, "'ldap' module is not installed")
class LdapPopulateTest(TestCase):
    def _get_mocked_ldap_user(self, attrs):
        class MockedLdapUser(object):
            @property
            def attrs(self):
                return attrs

        return MockedLdapUser()

    def test_manager_country_attribute_populate_country(self):
        ldap_attr = "c"
        override_settings = {"country": ldap_attr}
        user = factories.UserFactory()
        faked_ldap_user = self._get_mocked_ldap_user({ldap_attr: ["XXX"]})
        with self.settings(AUTH_LDAP_USER_ATTR_MAP=override_settings):
            manager_country_attribute_populate(None, user, faked_ldap_user)
            self.assertEqual(user.country, None)

    def test_manager_country_attribute_populate_unicode_in_manager(self):
        ldap_attr = "manager"
        override_settings = {"manager": ldap_attr}
        manager_names = [str("Żółcień"), str("John Smith")]
        user = factories.UserFactory()

        for manager_name in manager_names:
            faked_ldap_user = self._get_mocked_ldap_user(
                {ldap_attr: ["CN={},OU=XXX,DC=group".format(manager_name)]}
            )

            with self.settings(AUTH_LDAP_USER_ATTR_MAP=override_settings):
                manager_country_attribute_populate(None, user, faked_ldap_user)
            self.assertEqual(user.manager, manager_name)
            self.assertTrue(isinstance(user.manager, str))


class RalphUserAPITests(RalphAPITestCase):
    def test_get_user_list(self):
        url = reverse("ralphuser-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], RalphUser.objects.count())

    def test_get_user_details(self):
        region = Region.objects.create(name="EU")
        self.user1.regions.add(region)
        bo_asset_as_user = BackOfficeAssetFactory(user=self.user1)
        bo_asset_as_owner = BackOfficeAssetFactory(owner=self.user1)
        licence = LicenceFactory()
        LicenceUser.objects.create(licence=licence, user=self.user1)
        url = reverse("ralphuser-detail", args=(self.user1.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user1.username)
        self.assertEqual(response.data["first_name"], self.user1.first_name)
        self.assertEqual(response.data["last_name"], self.user1.last_name)
        self.assertEqual(response.data["regions"][0]["id"], region.id)
        self.assertEqual(
            response.data["assets_as_owner"][0]["id"], bo_asset_as_owner.id
        )
        self.assertEqual(response.data["assets_as_user"][0]["id"], bo_asset_as_user.id)
        self.assertEqual(response.data["licences"][0]["licence"]["id"], licence.id)

    def test_create_user_should_raise_method_not_allowed(self):
        url = reverse("ralphuser-list")
        data = {
            "username": "ralph",
            "first_name": "John",
            "last_name": "Snow",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_user(self):
        region = Region.objects.create(name="EU")
        url = reverse("ralphuser-detail", args=(self.user1.id,))
        data = {
            "first_name": "Ralph",
            "last_name": "Django",
            "regions": [region.id],
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "Ralph")
        self.assertEqual(self.user1.last_name, "Django")
        self.assertIn(region, self.user1.regions.all())

    def test_patch_user_when_user_is_not_superuser_should_raise_forbidden(self):
        region = Region.objects.create(name="EU")
        self.client.force_authenticate(self.user2)
        url = reverse("ralphuser-detail", args=(self.user1.id,))
        data = {
            "first_name": "Ralph",
            "last_name": "Django",
            "regions": [region.id],
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StockTakingTests(TestCase, ClientMixin):
    def setUp(self):
        super().setUp()
        self.user1 = factories.UserFactory()
        self.user2 = factories.UserFactory()
        self.service_env = ServiceEnvironmentFactory()
        self.model = BackOfficeAssetModelFactory()
        self.warehouse = WarehouseFactory()
        self.warehouse.stocktaking_enabled = True
        self.warehouse.save()
        self.asset = BackOfficeAssetFactory(
            warehouse=self.warehouse,
            model=self.model,
        )
        self.asset.user = self.user1
        self.asset.save()

        self.base_tag = settings.INVENTORY_TAG
        if self.asset.warehouse.stocktaking_tag_suffix != "":
            self.base_tag = "{prefix}-{warehouse}".format(
                prefix=self.base_tag,
                warehouse=self.asset.warehouse.stocktaking_tag_suffix,
            )
        self.date_tag = None
        if settings.INVENTORY_TAG_APPEND_DATE:
            self.date_tag = "{base}_{date}".format(
                base=self.base_tag,
                date=date.today().isoformat(),
            )
        self.tags = [
            self.base_tag,
            settings.INVENTORY_TAG_USER,
            self.date_tag,
        ]

    def test_tag_asset(self):
        self.assertTrue(self.login_as_user(self.user1))
        response = self.client.post(
            reverse("inventory_tag"),
            {"asset_id": self.asset.id, "confirm_button": "Yes", "answer": "yes"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        for t in self.tags:
            self.assertIn(t, self.asset.tags.names())

    def test_ownership_verification(self):
        self.assertTrue(self.login_as_user(self.user2))
        response = self.client.post(
            reverse("inventory_tag"),
            {"asset_id": self.asset.id, "confirm_button": "Yes", "answer": "yes"},
            follow=True,
        )
        self.assertEqual(response.status_code, 403)


class RalphUserAdminTests(TestCase, ClientMixin):
    def setUp(self):
        super().setUp()
        self.admin = factories.UserFactory(is_superuser=True, is_staff=True)
        self.user = factories.UserFactory(is_staff=True)
        self.login_as_user(self.user)

    def test_change_permission_is_required_to_change_user_password(self):
        def make_request():
            url = reverse("admin:auth_user_password_change", args=(self.admin.pk,))
            return self.client.post(
                url, {"password1": new_password, "password2": new_password}
            )

        new_password = "password123"
        perm = Permission.objects.get(codename="view_ralphuser")
        self.user.user_permissions.add(perm)
        response = make_request()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        perm = Permission.objects.get(codename="change_ralphuser")
        self.user.user_permissions.add(perm)
        response = make_request()
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check if password is actually changed
        self.admin.refresh_from_db()
        check_password(new_password, self.admin.password)
