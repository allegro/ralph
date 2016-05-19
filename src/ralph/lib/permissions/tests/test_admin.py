from django.contrib.admin.sites import site
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from ralph.lib.permissions.tests._base import PermissionsTestMixin
from ralph.lib.permissions.tests.models import Article


class PermissionPerFieldAdminMixinTestCase(PermissionsTestMixin, TestCase):
    def setUp(self):
        self._create_users_and_articles()
        self.admin = site._registry[Article]
        self.request_factory = RequestFactory()
        self._all_fields = self.admin.fieldsets[0][1]['fields'][:]
        self.maxDiff = None

    def _get_list_display(self, user):
        request = self.request_factory.get('/')
        request.user = user
        return self.admin.get_list_display(request)

    def _get_fieldsets(self, user, obj=None):
        request = self.request_factory.get('/')
        request.user = user
        return self.admin.get_fieldsets(request, obj)

    def test_admin_list_display_for_superuser(self):
        list_display = self._get_list_display(self.superuser)
        self.assertEqual(list_display, self.admin.list_display)

    def test_admin_list_display_without_model_field(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_title_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_title_field'
        ))
        list_display = self._get_list_display(self.user2)
        user_list_display = self.admin.list_display[:]
        user_list_display.remove('title')
        self.assertEqual(list_display, user_list_display)

    def test_admin_list_display_without_model_callable(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_content_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_content_field'
        ))
        list_display = self._get_list_display(self.user2)
        user_list_display = self.admin.list_display[:]
        # permission to sample_non_model_field_with_permissions is set based
        # on content field
        user_list_display.remove('content')
        user_list_display.remove('sample_non_model_field_with_permissions')
        self.assertEqual(list_display, user_list_display)

    def test_admin_list_display_without_admin_field(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_custom_field_1_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_custom_field_1_field'
        ))
        list_display = self._get_list_display(self.user2)
        user_list_display = self.admin.list_display[:]
        # permission to sample_admin_field_with_permissions is set based
        # on custom_field_1 field
        user_list_display.remove('custom_field_1')
        user_list_display.remove('sample_admin_field_with_permissions')
        self.assertEqual(list_display, user_list_display)

    def test_admin_get_fieldsets_for_superuser(self):
        fieldsets = self._get_fieldsets(self.superuser)[0][1]['fields']
        self.assertEqual(fieldsets, self._all_fields)

    def test_admin_get_fieldsets_without_model_field(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_title_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_title_field'
        ))
        fieldsets = self._get_fieldsets(self.user2)[0][1]['fields']
        self._all_fields.remove('title')
        self.assertEqual(fieldsets, self._all_fields)

    def test_admin_get_fieldsets_without_model_callable(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_content_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_content_field'
        ))
        fieldsets = self._get_fieldsets(self.user2)[0][1]['fields']
        # permission to sample_non_model_field_with_permissions is set based
        # on content field
        self._all_fields.remove('content')
        self._all_fields.remove('sample_non_model_field_with_permissions')
        self.assertEqual(fieldsets, self._all_fields)

    def test_admin_get_fieldsets_without_admin_field(self):
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_custom_field_1_field'
        ))
        self.user2.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_custom_field_1_field'
        ))
        fieldsets = self._get_fieldsets(self.user2)[0][1]['fields']
        # permission to sample_admin_field_with_permissions is set based
        # on custom_field_1 field
        self._all_fields.remove('custom_field_1')
        self._all_fields.remove('sample_admin_field_with_permissions')
        self.assertEqual(fieldsets, self._all_fields)
