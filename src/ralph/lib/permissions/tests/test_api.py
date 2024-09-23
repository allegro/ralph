# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ralph.lib.permissions.tests._base import PermissionsTestMixin
from ralph.lib.permissions.tests.models import Foo


class PermissionsForObjectTests(PermissionsTestMixin, APITestCase):
    def setUp(self):
        self._create_users_and_articles()

    def test_filter_objects_list_should_return_only_visible_by_user(self):
        url = reverse('test-api:article-list')
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get_single_object_should_success_when_user_has_permissions(self):
        url = reverse('test-api:article-detail', args=(self.article_1.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_object_should_fail_when_user_doesnt_have_permissions(self):  # noqa
        url = reverse('test-api:article-detail', args=(self.article_2.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionsPerFieldTests(PermissionsTestMixin, APITestCase):
    def setUp(self):
        self._create_users_and_articles()

    def test_user_should_see_field_when_he_has_change_access_to_it(self):
        url = reverse('test-api:article-detail', args=(self.article_1.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['custom_field_1'], 'test value')

    def test_user_should_not_see_field_when_he_has_readonly_access_to_it(self):
        url = reverse('test-api:article-detail', args=(self.article_3.id,))
        self.client.force_authenticate(self.user3)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['custom_field_1'], 'test value 2')

    def test_user_should_not_see_field_when_he_has_no_access_to_it(self):
        url = reverse('test-api:article-detail', args=(self.article_1.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('custom_field_1', response.data)

    def test_user_should_update_field_when_he_has_change_access_to_it(self):
        url = reverse('test-api:article-detail', args=(self.article_1.id,))
        self.client.force_authenticate(self.user2)
        data = {'custom_field_1': 'value1'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article_1.refresh_from_db()
        self.assertEqual(self.article_1.custom_field_1, 'value1')

    def test_user_should_not_update_field_when_he_has_readonly_access_to_it(self):  # noqa
        url = reverse('test-api:article-detail', args=(self.article_3.id,))
        self.client.force_authenticate(self.user3)
        data = {'custom_field_1': 'value1'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.article_3.refresh_from_db()
        self.assertEqual(self.article_3.custom_field_1, 'test value 2')

    def test_user_should_not_update_field_when_he_has_no_access_to_it(self):
        url = reverse('test-api:article-detail', args=(self.article_1.id,))
        self.client.force_authenticate(self.user1)
        data = {'custom_field_1': 'value1'}
        response = self.client.patch(url, data, format='json')
        # notice that this field is silently ignored for this user (as any
        # passed value which is not serializer (model) field)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article_1.refresh_from_db()
        self.assertEqual(self.article_1.custom_field_1, 'test value')


@ddt
class RalphPermissionsTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.foo = Foo.objects.create(bar='rab')

        def create_user(name, **kwargs):
            params = dict(
                username=name,
                is_staff=True,
                is_active=True,
            )
            params.update(kwargs)
            return get_user_model().objects.create(**params)
        cls.user1 = create_user('user1')
        cls.user2 = create_user('user2')
        cls.user3 = create_user('user3')
        cls.user_not_staff = create_user('user_not_staff', is_staff=False)

        def add_perm(user, perm):
            user.user_permissions.add(Permission.objects.get(
                content_type=ContentType.objects.get_for_model(Foo),
                codename=perm
            ))
        add_perm(cls.user1, 'change_foo')
        add_perm(cls.user1, 'delete_foo')
        add_perm(cls.user2, 'add_foo')
        add_perm(cls.user_not_staff, 'change_foo')

    @unpack
    @data(
        ('user1',),
        ('user2',),
    )
    def test_user_should_get_model_when_he_has_any_permission(self, username):
        url = reverse('test-api:foo-list')
        self.client.force_authenticate(getattr(self, username))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_not_get_model_when_he_has_any_access(self):
        url = reverse('test-api:foo-list')
        self.client.force_authenticate(self.user3)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_not_get_model_when_he_is_not_staff(self):
        url = reverse('test-api:foo-list')
        self.client.force_authenticate(self.user_not_staff)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_add_model_when_he_has_add_access(self):
        url = reverse('test-api:foo-list')
        self.client.force_authenticate(self.user2)
        response = self.client.post(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_should_not_add_model_when_he_has_not_add_access(self):
        url = reverse('test-api:foo-list')
        self.client.force_authenticate(self.user1)
        response = self.client.post(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_patch_model_when_he_has_change_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_put_model_when_he_has_change_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_not_patch_model_when_he_has_not_change_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_not_put_model_when_he_has_not_change_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_delete_model_when_he_has_delete_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_should_not_delete_model_when_he_has_not_delete_access(self):
        url = reverse('test-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
