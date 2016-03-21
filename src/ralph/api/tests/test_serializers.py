# -*- coding: utf-8 -*-

from dj.choices import Choices
from rest_framework.test import APIRequestFactory

from ralph.api.relations import RalphHyperlinkedRelatedField, RalphRelatedField
from ralph.api.tests._base import RalphAPITestCase
from ralph.api.tests.api import CarSerializer, CarSerializer2, FooSerializer
from ralph.tests.models import Car, Foo, Manufacturer


class TestChoices(Choices):
    _ = Choices.Choice

    foo = _('foo11')
    bar = _('bar22')


class TestStrSerialization(RalphAPITestCase):
    def setUp(self):
        self.foo = Foo(bar='abc')
        self.request_factory = APIRequestFactory()

    def test_str_field(self):
        request = self.request_factory.get('/api/foos')
        serializer = FooSerializer(self.foo,  context={'request': request})
        self.assertEqual(serializer.data['__str__'], str(self.foo))

    def test_str_field_with_type(self):
        request = self.request_factory.get('/api/foos')
        serializer = FooSerializer(self.foo,  context={'request': request})
        self.assertEqual(
            serializer.data['str_with_type'],
            '{}: {}'.format(Foo._meta.model_name, str(self.foo))
        )


class TestRalphSerializer(RalphAPITestCase):
    def setUp(self):
        self.manufacturer = Manufacturer(name="Tesla", country="USA")
        self.car = Car(manufacturer=self.manufacturer, name="S", year=2012)
        self.request_factory = APIRequestFactory()

    def test_get_serializer_related_field_when_safe_request(self):
        request = self.request_factory.get('/api/cars')
        car_serializer = CarSerializer(
            instance=self.car, context={'request': request}
        )
        self.assertEqual(
            car_serializer.serializer_related_field,
            RalphHyperlinkedRelatedField
        )

    def test_get_serializer_related_field_when_not_safe_request(self):
        request = self.request_factory.patch('/api/cars', data={})
        car_serializer = CarSerializer(
            instance=self.car, context={'request': request}
        )
        self.assertEqual(
            car_serializer.serializer_related_field,
            RalphRelatedField
        )

    def test_serializer_request_assigned_to_related_field(self):
        request = self.request_factory.patch('/api/cars', data={})
        request.user = self.user1
        car_serializer = CarSerializer(
            instance=self.car, context={'request': request}
        )
        fields = car_serializer.get_fields()
        self.assertIs(fields['year'].context['request'], request)
        self.assertIs(fields['manufacturer'].context['request'], request)

    def test_serializer_request_assigned_to_related_declared_field(self):
        request = self.request_factory.patch('/api/cars', data={})
        request.user = self.user1
        car_serializer = CarSerializer2(
            instance=self.car, context={'request': request}
        )
        fields = car_serializer.get_fields()
        self.assertIs(fields['year'].context['request'], request)
        self.assertIs(fields['manufacturer'].context['request'], request)
