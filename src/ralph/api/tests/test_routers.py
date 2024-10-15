# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ralph.api.tests._base import APIPermissionsTestMixin


class RalphRouterTests(APIPermissionsTestMixin, APITestCase):
    def test_router_user_has_access_to_foo(self):
        url = reverse("test-ralph-api:api-root")
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("foos", response.data)

    def test_router_user_has_not_access_to_foo(self):
        url = reverse("test-ralph-api:api-root")
        self.client.force_authenticate(self.user3)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("foos", response.data)

    def test_router_user_not_staff_has_not_access_to_foo(self):
        url = reverse("test-ralph-api:api-root")
        self.client.force_authenticate(self.user_not_staff)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn("foos", response.data)
