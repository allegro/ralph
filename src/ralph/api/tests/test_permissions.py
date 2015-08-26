# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ralph.api.tests._base import APIPermissionsTestMixin


@ddt
class RalphPermissionsTests(APIPermissionsTestMixin, APITestCase):
    @unpack
    @data(
        ('user1',),
        ('user2',),
    )
    def test_user_should_get_model_when_he_has_any_permission(self, username):
        url = reverse('test-ralph-api:foo-list')
        self.client.force_authenticate(getattr(self, username))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_not_get_model_when_he_has_any_access(self):
        url = reverse('test-ralph-api:foo-list')
        self.client.force_authenticate(self.user3)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_not_get_model_when_he_is_not_staff(self):
        url = reverse('test-ralph-api:foo-list')
        self.client.force_authenticate(self.user_not_staff)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_add_model_when_he_has_add_access(self):
        url = reverse('test-ralph-api:foo-list')
        self.client.force_authenticate(self.user2)
        response = self.client.post(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_should_not_add_model_when_he_has_not_add_access(self):
        url = reverse('test-ralph-api:foo-list')
        self.client.force_authenticate(self.user1)
        response = self.client.post(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_patch_model_when_he_has_change_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_put_model_when_he_has_change_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_should_not_patch_model_when_he_has_not_change_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_not_put_model_when_he_has_not_change_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.patch(url, {'bar': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_should_delete_model_when_he_has_delete_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user1)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_should_not_delete_model_when_he_has_not_delete_access(self):
        url = reverse('test-ralph-api:foo-detail', args=(self.foo.id,))
        self.client.force_authenticate(self.user2)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
