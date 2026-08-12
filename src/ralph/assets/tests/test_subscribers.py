# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.models import Service
from ralph.assets.subscribers import ACTION_TYPE
from ralph.assets.tests.factories import ServiceEnvironmentFactory, ServiceFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from django.test.utils import override_settings


@unittest.skipUnless(settings.ENABLE_HERMES_INTEGRATION, reason="Hermes integration is disabled")
@override_settings(HERMES_SERVICE_SYNC_COMPONENTS_TYPES=["service", "third party system"])
class ServiceSubscribersTestCase(TestCase):
    def setUp(self):
        super().setUp()
        for i in range(1, 4):
            UserFactory(username="business_user{}".format(i))
            UserFactory(username="technical_user{}".format(i))

    def _make_request(self, event_data, subscriber_name):
        response = self.client.post(
            reverse("hermes-event-subscriber", kwargs={"subscriber_name": subscriber_name}),
            json.dumps(event_data),
            content_type="application/json",
            follow=False,
        )
        return response

    def test_update_service_when_service_does_not_exist(self):
        data = {
            "actionType": "update",
            "uid": "sc-001",
            "type": "service",
            "name": "TestName",
            "status": "Active",
            "isActive": True,
            "environments": ["prod", "dev"],
            "businessOwners": [{"username": "business_user1"}],
            "technicalOwners": [{"username": "technical_user2"}],
            "area": {"name": "new area", "profitCenter": "test-PC"},
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        service = Service.objects.get(uid="sc-001")
        self.assertTrue(service.active)
        self.assertEqual(service.name, "TestName")
        self.assertEqual(service.business_segment.name, "new area")
        self.assertEqual(service.profit_center.name, "test-PC")
        self.assertCountEqual(["prod", "dev"], [env.name for env in service.environments.all()])
        self.assertCountEqual(
            ["business_user1"],
            [user.username for user in service.business_owners.all()],
        )
        self.assertCountEqual(
            ["technical_user2"],
            [user.username for user in service.technical_owners.all()],
        )

    def test_update_service_when_service_exist(self):
        service = ServiceFactory(
            business_segment__name="existing area",
            profit_center__name="existing PC",
        )
        service.business_owners.add(UserFactory(username="business_user1"))
        service.technical_owners.add(UserFactory(username="technical_user2"))
        ServiceEnvironmentFactory(service=service, environment__name="prod")
        data = {
            "actionType": "update",
            "uid": service.uid,
            "type": "service",
            "name": "New name",
            "status": "Active",
            "isActive": True,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user3"}],
            "technicalOwners": [{"username": "technical_user3"}],
            "area": {"name": "new area", "profitCenter": "new-PC"},
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        service.refresh_from_db()
        self.assertEqual(service.name, "New name")
        self.assertEqual(service.business_segment.name, "new area")
        self.assertEqual(service.profit_center.name, "new-PC")
        self.assertCountEqual(["dev"], [env.name for env in service.environments.all()])
        self.assertCountEqual(
            ["business_user3"],
            [user.username for user in service.business_owners.all()],
        )
        self.assertCountEqual(
            ["technical_user3"],
            [user.username for user in service.technical_owners.all()],
        )

    def test_create_third_party_system(self):
        service_uid = "sc-64564"
        data = {
            "actionType": "create",
            "uid": service_uid,
            "type": "third party system",
            "name": "Some third party system",
            "status": "Active",
            "isActive": True,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user3"}],
            "technicalOwners": [{"username": "technical_user3"}],
            "area": {"name": "new area", "profitCenter": "new-PC"},
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        service = Service.objects.get(uid=service_uid)
        self.assertTrue(service.active)
        self.assertEqual(service.name, "Some third party system")

    def test_create_service_of_unknown_type_doesnt_create(self):
        service_uid = "sc-64561"
        data = {
            "actionType": "create",
            "uid": service_uid,
            "type": "some weird type",
            "name": "Some service with weird type",
            "status": "Active",
            "isActive": True,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user3"}],
            "technicalOwners": [{"username": "technical_user3"}],
            "area": {"name": "new area", "profitCenter": "new-PC"},
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Service.DoesNotExist):
            Service.objects.get(uid=service_uid)

    def test_create_service_change_to_unknown_type_then_change_back_works(self):
        service_uid = "sc-64562"
        data = {
            "actionType": "create",
            "uid": service_uid,
            "type": "service",
            "name": "This will change types",
            "status": "Active",
            "isActive": True,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user3"}],
            "technicalOwners": [{"username": "technical_user3"}],
            "area": {"name": "new area", "profitCenter": "new-PC"},
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        self.assertIsNotNone(Service.objects.get(uid=service_uid))
        data["actionType"] = "update"
        data["type"] = "some weird type"
        data["name"] = "This has new type"
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Service.objects.get(uid=service_uid).name, "This has new type")
        data["type"] = "service"
        data["name"] = "This has old type"
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Service.objects.get(uid=service_uid).name, "This has old type")

    @patch("ralph.assets.subscribers.logger")
    def test_update_service_environment_when_environment_assigned_to_object(self, mock_logger):
        service = ServiceFactory(active=True)
        service_env = ServiceEnvironmentFactory(service=service, environment__name="prod")
        DataCenterAssetFactory(service_env=service_env)
        data = {
            "actionType": "update",
            "uid": service.uid,
            "type": "service",
            "name": "New name",
            "status": "Active",
            "isActive": False,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user3"}],
            "technicalOwners": [{"username": "technical_user3"}],
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        service.refresh_from_db()
        mock_logger.error.assert_called_with(
            "Can not delete service environment - it has assigned some base objects",  # noqa: E501
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": service.uid,
                "service_name": service.name,
            },
        )
        service.refresh_from_db()
        self.assertTrue(service.active)

    def test_delete_with_valid_event_data(self):
        service = ServiceFactory(active=True)
        data = {
            "actionType": "delete",
            "uid": service.uid,
            "type": "service",
            "name": "Service name",
            "status": "Inactive",
            "isActive": False,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user1"}],
            "technicalOwners": [{"username": "technical_user1"}],
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        service.refresh_from_db()
        self.assertFalse(service.active)

    @patch("ralph.assets.subscribers.logger")
    def test_delete_service_when_service_assigned_to_object(self, mock_logger):
        service = ServiceFactory(active=True)
        service_env = ServiceEnvironmentFactory(service=service)
        DataCenterAssetFactory(service_env=service_env)
        data = {
            "actionType": "delete",
            "uid": service.uid,
            "type": "service",
            "name": "Service name",
            "status": "Inactive",
            "isActive": False,
            "environments": ["dev"],
            "businessOwners": [{"username": "business_user"}],
            "technicalOwners": [{"username": "technical_user"}],
        }
        response = self._make_request(data, settings.HERMES_SERVICE_TOPICS["UPDATE"])
        self.assertEqual(response.status_code, 204)
        mock_logger.error.assert_called_with(
            "Can not delete service - it has assigned some base objects",
            extra={
                "action_type": ACTION_TYPE,
                "service_uid": data["uid"],
                "service_name": data["name"],
            },
        )
        service.refresh_from_db()
        self.assertTrue(service.active)
