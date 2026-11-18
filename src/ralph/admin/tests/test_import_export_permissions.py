# -*- coding: utf-8 -*-
from importlib import import_module
from unittest.mock import patch

import tablib
from ddt import data, ddt
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from import_export.formats import base_formats

from ralph.accounts.models import RalphUser, Region
from ralph.accounts.tests.factories import RegionFactory
from ralph.admin.mixins import RalphAdminImportExportMixin
from ralph.admin.sites import ralph_site
from ralph.admin.tests.tests_views import FACTORY_MAP
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.data_importer.resources import BaseObjectsSupportRichResource
from ralph.lib.permissions.import_export import restrict_resource_class
from ralph.lib.visibility_scope.tests import ServiceBasedVisibilityScopeFactory
from ralph.licences.models import Licence
from ralph.supports.models import Support
from ralph.tests import factories
from ralph.tests.mixins import ClientMixin

IMPORT_EXPORT_FACTORY_MAP: dict[str, str | None]  = {
    **FACTORY_MAP,
    # models without factories (or with factories which could not be used
    # here) - only access to import/export views is checked for them
    "django.contrib.contenttypes.models.ContentType": None,
    "ralph.assets.models.assets.Asset": None,
    "ralph.assets.models.base.BaseObject": None,
    "ralph.assets.models.components.GenericComponent": None,
    "ralph.deployment.models.Deployment": None,
    "ralph.deployment.models.PrebootFile": None,
    "ralph.deployment.models.PrebootItem": None,
    "ralph.networks.models.networks.DiscoveryQueue": None,
    "ralph.switchports.models.validation.SwitchportRefreshJob": None,
}


def _model_path(model):
    return "{}.{}".format(model.__module__, model.__name__)


IMPORT_EXPORT_MODELS = sorted(
    _model_path(model)
    for model, model_admin in ralph_site._registry.items()
    if isinstance(model_admin, RalphAdminImportExportMixin)
    and not model.__module__.startswith("ralph.tests.")
)


def _import_string(path):
    module_path, name = path.rsplit(".", 1)
    return getattr(import_module(module_path), name)


def _format_index(formats, format_class):
    return str(list(formats).index(format_class))


@ddt
class ImportExportPermissionsForAllModelsTestCase(TestCase):
    """
    For every model with import/export enabled in admin check that:
    * superuser and user with all permissions could export and import
    * user with view permissions only could export, but not import
    * user without permissions could not export nor import
    """

    @classmethod
    def setUpTestData(cls):
        ContentType.objects.get_for_models(*ralph_site._registry.keys())
        permissions = list(Permission.objects.all())

        cls.admin_user = factories.UserFactory(is_staff=True, is_superuser=True)
        cls.full_user = factories.UserFactory(is_staff=True)
        cls.full_user.user_permissions.set(permissions)
        cls.readonly_user = factories.UserFactory(is_staff=True)
        cls.readonly_user.user_permissions.set(
            permission for permission in permissions if permission.codename.startswith("view_")
        )
        cls.no_permissions_user = factories.UserFactory(is_staff=True)

    def _get_model(self, model_path):
        self.assertIn(
            model_path,
            IMPORT_EXPORT_FACTORY_MAP,
            msg="Add factory for {} to IMPORT_EXPORT_FACTORY_MAP".format(model_path),
        )
        return _import_string(model_path)

    def _create_object(self, model_path) -> models.Model | None:
        if factory_path := IMPORT_EXPORT_FACTORY_MAP[model_path]:
            obj = _import_string(factory_path)()
            # give access to objects with region-based permissions
            regions = Region.objects.all()
            self.full_user.regions.add(*regions)
            self.readonly_user.regions.add(*regions)
            return obj
        else:
            return None

    def _login(self, user):
        # fresh client (and session) for every user
        self.client = Client()
        self.client.force_login(user)

    def _url(self, model, action):
        return reverse(
            "admin:{}_{}_{}".format(model._meta.app_label, model._meta.model_name, action)
        )

    def _request(self, user):
        request = RequestFactory().get("/")
        request.user = user
        return request

    def _export_post_data(self, model_admin, user):
        formats = model_admin.get_export_formats()
        resources = model_admin.get_export_resource_classes(self._request(user))
        form = model_admin.get_export_form_class()(formats, resources)
        post_data = {"format": _format_index(formats, base_formats.CSV)}
        for name, field in form.fields.items():
            if getattr(field, "is_selectable_field", False):
                post_data[name] = "on"
        return post_data

    def _assert_can_export(self, model, model_admin, user, obj):
        url = self._url(model, "export")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, self._export_post_data(model_admin, user))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.get("Content-Disposition", "").startswith("attachment"),
            msg="Export file not returned",
        )
        if obj is not None:
            dataset = tablib.Dataset().load(response.content.decode("utf-8"), format="csv")
            self.assertGreaterEqual(len(dataset), 1, msg="Exported object not found")

    def _assert_cannot_export(self, model, model_admin, user):
        url = self._url(model, "export")
        self.assertEqual(self.client.get(url).status_code, 403)
        response = self.client.post(url, self._export_post_data(model_admin, user))
        self.assertEqual(response.status_code, 403)

    def _assert_can_import(self, model, model_admin, obj):
        url = self._url(model, "import")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        if obj is None:
            return

        # update existing object (without changing any data)
        formats = model_admin.get_import_formats()
        import_file = SimpleUploadedFile(
            "import.csv",
            "id\n{}\n".format(obj.pk).encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(
            url,
            {
                "import_file": import_file,
                "format": _format_index(formats, base_formats.CSV),
            },
        )
        self.assertEqual(response.status_code, 200)
        confirm_form = response.context.get("confirm_form")
        result = response.context.get("result")
        self.assertIsNotNone(confirm_form, msg=self._import_errors(response, result))

        with patch.object(
            model_admin, "process_result", wraps=model_admin.process_result
        ) as process_result:
            response = self.client.post(self._url(model, "process_import"), confirm_form.initial)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(process_result.called, msg="Import not processed")
        result = process_result.call_args[0][0]
        self.assertEqual(
            result.totals["update"],
            1,
            msg="Object not updated by import: {}".format(dict(result.totals)),
        )

    def _import_errors(self, response, result):
        if result is None:
            return "Import form errors: {}".format(response.context["form"].errors)
        errors = [str(error.error) for error in result.base_errors]
        for row in result.rows:
            errors.extend(str(error.error) for error in row.errors)
        errors.extend(str(row.error_dict) for row in result.invalid_rows)
        return "Import dry run failed: {}".format(errors)

    def _assert_cannot_import(self, model):
        self.assertEqual(self.client.get(self._url(model, "import")).status_code, 403)
        response = self.client.post(self._url(model, "process_import"), {})
        self.assertEqual(response.status_code, 403)

    @data(*IMPORT_EXPORT_MODELS)
    def test_import_export_permissions(self, model_path):
        model = self._get_model(model_path)
        model_admin = ralph_site._registry[model]
        obj = self._create_object(model_path)
        # import / export could be disabled for everyone (`import_enabled`,
        # `export_enabled` or `has_add_permission` returning False)
        import_enabled = model_admin.has_import_permission(self._request(self.admin_user))
        export_enabled = model_admin.has_export_permission(self._request(self.admin_user))

        for user_attribute in ("admin_user", "full_user"):
            with self.subTest(user=user_attribute):
                user = getattr(self, user_attribute)
                self._login(user)
                if export_enabled:
                    self._assert_can_export(model, model_admin, user, obj)
                else:
                    self._assert_cannot_export(model, model_admin, user)
                if import_enabled:
                    self._assert_can_import(model, model_admin, obj)
                else:
                    self._assert_cannot_import(model)

        with self.subTest(user="readonly_user"):
            self._login(self.readonly_user)
            if export_enabled:
                self._assert_can_export(model, model_admin, self.readonly_user, obj)
            else:
                self._assert_cannot_export(model, model_admin, self.readonly_user)
            self._assert_cannot_import(model)

        with self.subTest(user="no_permissions_user"):
            self._login(self.no_permissions_user)
            self._assert_cannot_export(model, model_admin, self.no_permissions_user)
            self._assert_cannot_import(model)


class ImportExportPermissionsTestCase(ClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = factories.UserFactory(is_superuser=True, is_staff=True)
        self.user = factories.UserFactory(is_staff=True)
        self.login_as_user(self.user)
        self.model_admin = ralph_site._registry[RalphUser]

    def _add_perms(self, *codenames):
        self.user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
        # clear permissions cache
        self.user = RalphUser.objects.get(pk=self.user.pk)

    def _request(self):
        request = RequestFactory().get("/")
        request.user = self.user
        return request

    def _url(self, action):
        return reverse("admin:accounts_ralphuser_{}".format(action))

    def test_export_without_view_permission_is_forbidden(self):
        response = self.client.get(self._url("export"))
        self.assertEqual(response.status_code, 403)

    def test_import_without_permissions_is_forbidden(self):
        response = self.client.get(self._url("import"))
        self.assertEqual(response.status_code, 403)
        response = self.client.post(self._url("process_import"), {})
        self.assertEqual(response.status_code, 403)

    def test_import_with_view_permission_only_is_forbidden(self):
        self._add_perms("view_ralphuser")
        response = self.client.get(self._url("export"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self._url("import"))
        self.assertEqual(response.status_code, 403)
        response = self.client.post(self._url("process_import"), {})
        self.assertEqual(response.status_code, 403)

    def test_import_with_add_and_change_permissions_is_allowed(self):
        self._add_perms("add_ralphuser", "change_ralphuser")
        response = self.client.get(self._url("import"))
        self.assertEqual(response.status_code, 200)

    def test_export_contains_only_fields_with_view_permission(self):
        self._add_perms(
            "view_ralphuser",
            "view_ralphuser_username_field",
            "view_ralphuser_email_field",
        )
        resource = self.model_admin.get_export_resource_classes(self._request())[0]()
        headers = resource.get_export_headers()
        self.assertIn("id", headers)
        self.assertIn("username", headers)
        self.assertIn("email", headers)
        self.assertNotIn("password", headers)
        self.assertNotIn("is_superuser", headers)
        self.assertNotIn("first_name", headers)

    def test_password_is_never_exported(self):
        self.user = self.admin_user
        resource = self.model_admin.get_export_resource_classes(self._request())[0]()
        headers = resource.get_export_headers()
        self.assertIn("is_superuser", headers)
        self.assertNotIn("password", headers)

    def test_import_column_without_change_permission_is_rejected(self):
        self._add_perms(
            "add_ralphuser",
            "change_ralphuser",
            "change_ralphuser_first_name_field",
        )
        resource = self.model_admin.get_import_resource_classes(self._request())[0]()
        dataset = tablib.Dataset(headers=["id", "is_superuser"])
        dataset.append([self.user.pk, 1])
        result = resource.import_data(dataset, dry_run=False, user=self.user)
        self.assertTrue(result.has_errors())
        self.assertIsInstance(result.base_errors[0].error, PermissionDenied)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)

    def test_import_column_with_change_permission_is_allowed(self):
        self._add_perms(
            "add_ralphuser",
            "change_ralphuser",
            "change_ralphuser_first_name_field",
        )
        resource = self.model_admin.get_import_resource_classes(self._request())[0]()
        dataset = tablib.Dataset(headers=["id", "first_name"])
        dataset.append([self.admin_user.pk, "John"])
        result = resource.import_data(dataset, dry_run=False, user=self.user)
        self.assertFalse(result.has_errors())
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.first_name, "John")

    def test_disabled_import_and_export_are_forbidden_even_for_superuser(self):
        self.login_as_user(self.admin_user)
        with patch.object(self.model_admin, "import_enabled", False), patch.object(
            self.model_admin, "export_enabled", False
        ):
            self.assertEqual(self.client.get(self._url("export")).status_code, 403)
            self.assertEqual(self.client.get(self._url("import")).status_code, 403)
            response = self.client.post(self._url("process_import"), {})
            self.assertEqual(response.status_code, 403)

    def test_password_could_not_be_imported_even_by_superuser(self):
        self.user = self.admin_user
        resource = self.model_admin.get_import_resource_classes(self._request())[0]()
        dataset = tablib.Dataset(headers=["id", "password"])
        dataset.append([self.admin_user.pk, "plain"])
        result = resource.import_data(dataset, dry_run=False, user=self.user)
        self.assertTrue(result.has_errors())
        self.admin_user.refresh_from_db()
        self.assertNotEqual(self.admin_user.password, "plain")


class ComputedFieldsPermissionsTestCase(TestCase):
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
        self.user.user_permissions.add(
            *Permission.objects.filter(
                codename__in=["view_baseobjectssupport", "view_support"]
            )
        )
        self.user = RalphUser.objects.get(pk=self.user.pk)

    def _export_headers(self):
        resource_class = restrict_resource_class(
            BaseObjectsSupportRichResource, self.user, "view"
        )
        return resource_class().get_export_headers()

    def test_computed_price_is_hidden_without_price_permission(self):
        headers = self._export_headers()
        self.assertNotIn("support__price", headers)
        self.assertNotIn("support__price_per_object", headers)

    def test_computed_price_is_exported_with_price_permission(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_support_price_field")
        )
        self.user = RalphUser.objects.get(pk=self.user.pk)
        headers = self._export_headers()
        self.assertIn("support__price", headers)
        self.assertIn("support__price_per_object", headers)


class ImportExportRelatedPermissionsMixin:
    def _make_user(self, *codenames, content_types=()):
        user = factories.UserFactory(is_staff=True)
        permissions = list(Permission.objects.filter(codename__in=codenames))
        if content_types:
            permissions += Permission.objects.filter(
                content_type__in=[ContentType.objects.get_for_model(m) for m in content_types]
            )
        user.user_permissions.add(*permissions)
        return RalphUser.objects.get(pk=user.pk)

    def _request(self, user):
        request = RequestFactory().get("/")
        request.user = user
        return request

    def _export_headers(self, model, user):
        model_admin = ralph_site._registry[model]
        resource = model_admin.get_export_resource_classes(self._request(user))[0]()
        return resource.get_export_headers()

    def _import(self, model, user, headers, row):
        model_admin = ralph_site._registry[model]
        resource = model_admin.get_import_resource_classes(self._request(user))[0]()
        dataset = tablib.Dataset(headers=headers)
        dataset.append(row)
        return resource.import_data(dataset, dry_run=False, user=user)


@ddt
class BaseObjectsFieldPermissionsTestCase(ImportExportRelatedPermissionsMixin, TestCase):
    @data(
        (Support, "support"),
        (Licence, "licence"),
    )
    def test_export_requires_base_objects_field_permission(self, params):
        model, name = params
        user = self._make_user("view_{}".format(name))
        headers = self._export_headers(model, user)
        self.assertNotIn("base_objects", headers)
        self.assertNotIn("base_objects_str", headers)

        user = self._make_user("view_{}".format(name), "view_{}_base_objects_field".format(name))
        headers = self._export_headers(model, user)
        self.assertIn("base_objects", headers)
        self.assertIn("base_objects_str", headers)

    @data(
        (Support, "support"),
        (Licence, "licence"),
    )
    def test_import_requires_base_objects_field_permission(self, params):
        model, name = params
        user = self._make_user("add_{}".format(name), "change_{}".format(name))
        result = self._import(model, user, ["id", "base_objects"], [1, ""])
        self.assertTrue(result.has_errors())
        self.assertIsInstance(result.base_errors[0].error, PermissionDenied)

        user = self._make_user(
            "add_{}".format(name),
            "change_{}".format(name),
            "change_{}_base_objects_field".format(name),
        )
        result = self._import(model, user, ["id", "base_objects"], [1, ""])
        self.assertFalse(result.base_errors)


class PolymorphicRelatedObjectsPermissionsTestCase(ImportExportRelatedPermissionsMixin, TestCase):
    def setUp(self):
        self.region = RegionFactory()
        self.other_region = RegionFactory()
        self.user = self._make_user(content_types=[BackOfficeAsset])
        self.user.regions.add(self.region)
        self.user = RalphUser.objects.get(pk=self.user.pk)
        self.asset = BackOfficeAssetFactory(region=self.region)

    def test_parent_from_other_region_is_rejected(self):
        parent = BackOfficeAssetFactory(region=self.other_region)
        result = self._import(
            BackOfficeAsset, self.user, ["id", "parent"], [self.asset.pk, parent.pk]
        )
        self.assertTrue(result.has_errors())
        self.asset.refresh_from_db()
        self.assertIsNone(self.asset.parent_id)

    def test_parent_from_own_region_is_accepted(self):
        parent = BackOfficeAssetFactory(region=self.region)
        result = self._import(
            BackOfficeAsset, self.user, ["id", "parent"], [self.asset.pk, parent.pk]
        )
        self.assertFalse(result.has_errors())
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.parent_id, parent.pk)


class ImportVisibilityScopeTestCase(ImportExportRelatedPermissionsMixin, TestCase):
    def setUp(self):
        self.service_env_in_scope = ServiceEnvironmentFactory()
        self.service_env_outside_scope = ServiceEnvironmentFactory()
        scope = ServiceBasedVisibilityScopeFactory()
        scope.services.set([self.service_env_in_scope.service])
        self.scoped_user = self._make_user(content_types=[DataCenterAsset])
        scope.users.set([self.scoped_user])
        self.unscoped_user = self._make_user(content_types=[DataCenterAsset])
        self.asset_in_scope = DataCenterAssetFactory(
            service_env=self.service_env_in_scope, remarks="old"
        )
        self.asset_outside_scope = DataCenterAssetFactory(
            service_env=self.service_env_outside_scope, remarks="old"
        )

    def test_asset_in_scope_could_be_updated(self):
        result = self._import(
            DataCenterAsset,
            self.scoped_user,
            ["id", "remarks"],
            [self.asset_in_scope.pk, "new"],
        )
        self.assertFalse(result.has_errors())
        self.asset_in_scope.refresh_from_db()
        self.assertEqual(self.asset_in_scope.remarks, "new")

    def test_asset_outside_scope_could_not_be_updated(self):
        result = self._import(
            DataCenterAsset,
            self.scoped_user,
            ["id", "remarks"],
            [self.asset_outside_scope.pk, "new"],
        )
        self.assertTrue(result.has_errors())
        self.asset_outside_scope.refresh_from_db()
        self.assertEqual(self.asset_outside_scope.remarks, "old")

    def test_user_without_scope_could_update_any_asset(self):
        result = self._import(
            DataCenterAsset,
            self.unscoped_user,
            ["id", "remarks"],
            [self.asset_outside_scope.pk, "new"],
        )
        self.assertFalse(result.has_errors())
        self.asset_outside_scope.refresh_from_db()
        self.assertEqual(self.asset_outside_scope.remarks, "new")
