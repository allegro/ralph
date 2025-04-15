import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TransactionTestCase
from django.urls import reverse
from factory.django import DjangoModelFactory
from rest_framework.test import APITestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import ServiceEnvironmentFactory, ServiceFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.lib.visibility_scope.models import ServiceBasedVisibilityScope
from ralph.supports.models import BaseObjectsSupport, Support
from ralph.virtual.models import VirtualServer


class ServiceBasedVisibilityScopeFactory(DjangoModelFactory):
    name = factory.sequence(lambda n: "Information Bubble {}".format(n))

    class Meta:
        model = ServiceBasedVisibilityScope
        django_get_or_create = ["name"]


class TestServiceBasedVisibilityScopeCreation(TransactionTestCase):
    def test_create_visibility_scope(self):
        vs = ServiceBasedVisibilityScopeFactory(name="foo")
        vs.services.set([ServiceFactory(), ServiceFactory()])
        self.assertEqual(len(vs.services.all()), 2)

    def test_assign_user_to_visibility_scope(self):
        vs = ServiceBasedVisibilityScopeFactory(name="foo")
        vs.services.set([ServiceFactory(), ServiceFactory()])
        user = UserFactory()
        vs.users.set([user])
        self.assertEqual(user.service_visibility_scopes.first().pk, vs.pk)


class TestServiceBasedVisibilityScopeVisibility(APITestCase):
    def setUp(self):
        super().setUp()
        self.visibility_scope = ServiceBasedVisibilityScopeFactory(name="foo")

        self.service_env_in_visibility_scope = ServiceEnvironmentFactory()
        self.service_in_visibility_scope = self.service_env_in_visibility_scope.service
        self.visibility_scope.services.set([self.service_in_visibility_scope])

        self.service_env_outside_visibility_scope = ServiceEnvironmentFactory()
        self.service_outside_visibility_scope = (
            self.service_env_outside_visibility_scope.service
        )

        self.user_outside_visibility_scope = get_user_model().objects.create(
            username="user1", is_staff=True, is_active=True
        )
        self.user_in_visibility_scope = get_user_model().objects.create(
            username="user2", is_staff=True, is_active=True
        )

        content_types = [
            ContentType.objects.get_for_model(m)
            for m in (DataCenterAsset, VirtualServer, Support, BaseObjectsSupport)
        ]
        permissions = Permission.objects.filter(content_type__in=content_types)
        for user in (self.user_in_visibility_scope, self.user_outside_visibility_scope):
            user.user_permissions.add(*permissions)

        self.visibility_scope.users.set([self.user_in_visibility_scope])


class TestDataCenterAssetVisibilityInVisibilityScope(
    TestServiceBasedVisibilityScopeVisibility
):
    def setUp(self):
        super().setUp()
        self.hw_in_visibility_scope = DataCenterAssetFactory(
            service_env=self.service_env_in_visibility_scope
        )
        self.hw_outside_visibility_scope = DataCenterAssetFactory(
            service_env=self.service_env_outside_visibility_scope
        )
        self.hw_without_service_env = DataCenterAssetFactory(service_env=None)

        permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(DataCenterAsset)
        )
        for user in (self.user_in_visibility_scope, self.user_outside_visibility_scope):
            user.user_permissions.add(*permissions)

    def test_user_in_visibility_scope_can_see_1_hw(self):
        self.client.force_authenticate(self.user_in_visibility_scope)
        url = reverse("datacenterasset-list")
        response = self.client.get(url)
        self.assertEqual(response.json()["count"], 1)

    def test_user_outside_visibility_scope_can_see_3_hws(self):
        self.client.force_authenticate(self.user_outside_visibility_scope)
        url = reverse("datacenterasset-list")
        response = self.client.get(url)
        self.assertEqual(response.json()["count"], 3)
