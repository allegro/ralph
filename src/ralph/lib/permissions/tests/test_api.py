# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ralph.lib.permissions.tests._base import PermissionsTestMixin


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
