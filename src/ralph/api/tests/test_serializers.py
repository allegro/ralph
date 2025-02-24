# -*- coding: utf-8 -*-

from dj.choices import Choices
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory
from reversion.models import Version

from ralph.accounts.tests.factories import RegionFactory
from ralph.api.relations import RalphHyperlinkedRelatedField, RalphRelatedField
from ralph.api.tests._base import RalphAPITestCase
from ralph.api.tests.api import CarSerializer, CarSerializer2, FooSerializer
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import BaseObjectLicence
from ralph.licences.tests.factories import LicenceFactory
from ralph.tests.models import Car, Foo, TestManufacturer


class TestChoices(Choices):
    _ = Choices.Choice

    foo = _("foo11")
    bar = _("bar22")


class TestStrSerialization(RalphAPITestCase):
    def setUp(self):
        self.foo = Foo(bar="abc")
        self.request_factory = APIRequestFactory()

    def test_str_field(self):
        request = self.request_factory.get("/api/foos")
        serializer = FooSerializer(self.foo, context={"request": request})
        self.assertEqual(serializer.data["__str__"], str(self.foo))

    def test_str_field_with_type(self):
        request = self.request_factory.get("/api/foos")
        serializer = FooSerializer(self.foo, context={"request": request})
        self.assertEqual(
            serializer.data["str_with_type"],
            "{}: {}".format(Foo._meta.model_name, str(self.foo)),
        )


class TestRalphSerializer(RalphAPITestCase):
    def setUp(self):
        self.manufacturer = TestManufacturer(name="Tesla", country="USA")
        self.car = Car(manufacturer=self.manufacturer, name="S", year=2012)
        self.request_factory = APIRequestFactory()

        get_user_model().objects.create_superuser("test", "test@test.test", "test")
        self.client = APIClient()
        self.client.login(username="test", password="test")

    def test_get_serializer_related_field_when_safe_request(self):
        request = self.request_factory.get("/api/cars")
        car_serializer = CarSerializer(instance=self.car, context={"request": request})
        self.assertEqual(
            car_serializer.serializer_related_field, RalphHyperlinkedRelatedField
        )

    def test_get_serializer_related_field_when_not_safe_request(self):
        request = self.request_factory.patch("/api/cars", data={})
        car_serializer = CarSerializer(instance=self.car, context={"request": request})
        self.assertEqual(car_serializer.serializer_related_field, RalphRelatedField)

    def test_serializer_request_assigned_to_related_field(self):
        request = self.request_factory.patch("/api/cars", data={})
        request.user = self.user1
        car_serializer = CarSerializer(instance=self.car, context={"request": request})
        fields = car_serializer.get_fields()
        self.assertIs(fields["year"].context["request"], request)
        self.assertIs(fields["manufacturer"].context["request"], request)

    def test_serializer_request_assigned_to_related_declared_field(self):
        request = self.request_factory.patch("/api/cars", data={})
        request.user = self.user1
        car_serializer = CarSerializer2(instance=self.car, context={"request": request})
        fields = car_serializer.get_fields()
        self.assertIs(fields["year"].context["request"], request)
        self.assertIs(fields["manufacturer"].context["request"], request)

    def test_reversion_history_save(self):
        response = self.client.post("/test-ralph-api/foos/", data={"bar": "bar_name"})
        foo = Foo.objects.get(pk=response.data["id"])
        history = Version.objects.get_for_object(foo)
        self.assertEqual(len(history), 1)
        self.assertIn("bar_name", history[0].serialized_data)

        response = self.client.patch(
            "/test-ralph-api/foos/{}/".format(foo.id), data={"bar": "new_bar"}
        )
        foo = Foo.objects.get(pk=response.data["id"])
        history = Version.objects.get_for_object(foo)
        self.assertEqual(len(history), 2)
        self.assertIn("new_bar", history[0].serialized_data)

    def test_reversion_history_for_intermediary_model(self):
        region_pl = RegionFactory()
        bo_asset = BackOfficeAssetFactory(region=region_pl)
        licence = LicenceFactory(region=region_pl)
        url = reverse("baseobjectlicence-list")
        response = self.client.post(
            url, data={"base_object": bo_asset.id, "licence": licence.id}
        )
        base_object_licence = BaseObjectLicence.objects.get(pk=response.data["id"])
        history = Version.objects.get_for_object(base_object_licence)
        self.assertEqual(len(history), 1)
        self.assertIn('"licence": {}'.format(licence.id), history[0].serialized_data)
