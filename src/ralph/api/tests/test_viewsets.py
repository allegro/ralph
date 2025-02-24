# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from rest_framework import relations
from rest_framework.test import APIClient, APIRequestFactory

from ralph.api.serializers import ReversedChoiceField
from ralph.api.tests.api import (
    Car,
    CarSerializer,
    CarViewSet,
    ManufacturerSerializer2,
    ManufacturerViewSet
)
from ralph.api.viewsets import RalphAPIViewSet
from ralph.tests import RalphTestCase
from ralph.tests.factories import TestManufacturerFactory


class ViewsetWithoutRalphPermission(RalphAPIViewSet):
    permission_classes = []


class ViewsetWithoutPermissionsForObjectFilter(RalphAPIViewSet):
    filter_backends = []


class TestRalphViewset(RalphTestCase):
    def setUp(self):
        super().setUp()
        self.request_factory = APIRequestFactory()
        self.manufacture_1 = TestManufacturerFactory(name="test", country="Poland")
        self.manufacture_2 = TestManufacturerFactory(name="test2", country="test")
        get_user_model().objects.create_superuser("test", "test@test.test", "test")
        self.client = APIClient()
        self.client.login(username="test", password="test")

    def test_should_raise_attributeerror_when_ralph_permission_missing(self):
        with self.assertRaises(AttributeError):
            ViewsetWithoutRalphPermission()

    def test_should_raise_attributeerror_when_permission_for_object_filter_missing(
        self,
    ):  # noqa
        with self.assertRaises(AttributeError):
            ViewsetWithoutPermissionsForObjectFilter()

    def test_get_serializer_class_should_return_base_when_safe_request(self):
        request = self.request_factory.get("/")
        cvs = CarViewSet()
        cvs.request = request
        self.assertEqual(cvs.get_serializer_class(), CarSerializer)

    def test_get_serializer_class_should_return_dynamic_when_not_safe_request(self):  # noqa
        request = self.request_factory.post("/")
        cvs = CarViewSet()
        cvs.request = request
        serializer_class = cvs.get_serializer_class()
        self.assertEqual(serializer_class.__name__, "CarSaveSerializer")
        self.assertEqual(serializer_class.Meta.model, Car)
        self.assertEqual(serializer_class.Meta.depth, 0)
        self.assertEqual(serializer_class.serializer_choice_field, ReversedChoiceField)
        self.assertEqual(
            serializer_class.serializer_related_field, relations.PrimaryKeyRelatedField
        )

    def test_get_serializer_class_should_return_defined_when_not_safe_request_and_save_serializer_class_defined(
        self,
    ):  # noqa
        request = self.request_factory.patch("/")
        mvs = ManufacturerViewSet()
        mvs.request = request
        self.assertEqual(mvs.get_serializer_class(), ManufacturerSerializer2)

    def test_options_filtering(self):
        response = self.client.options("/api/manufacturers/")
        self.assertCountEqual(
            response.data["filtering"],
            ["name", "manufacturer_kind"],
        )


class TestAdminSearchFieldsMixin(RalphTestCase):
    def test_get_filter_fields_from_admin(self):
        cvs = CarViewSet()
        self.assertEqual(
            cvs.filter_fields, ["manufacturer__name", "name", "foos__bar", "year"]
        )
