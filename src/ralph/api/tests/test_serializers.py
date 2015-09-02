# -*- coding: utf-8 -*-
from collections import OrderedDict

from dj.choices import Choices
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from ralph.api.relations import RalphHyperlinkedRelatedField, RalphRelatedField
from ralph.api.serializers import ReversedChoiceField
from ralph.api.tests._base import RalphAPITestCase
from ralph.api.tests.api import CarSerializer, CarSerializer2
from ralph.tests import RalphTestCase
from ralph.tests.models import Car, Manufacturer


class TestChoices(Choices):
    _ = Choices.Choice

    foo = _('foo11')
    bar = _('bar22')


class TestReversedChoiceField(RalphTestCase):
    def setUp(self):
        self.reversed_choice_field = ReversedChoiceField(TestChoices())

    def test_reversed_choices(self):
        self.assertEqual(
            self.reversed_choice_field.reversed_choices,
            OrderedDict([
                ('foo11', TestChoices.foo.id),
                ('bar22', TestChoices.bar.id)
            ])
        )

    def test_to_representation_should_return_choice_text(self):
        self.assertEqual(
            self.reversed_choice_field.to_representation(TestChoices.foo.id),
            'foo11'
        )

    def test_to_internal_value_should_map_choice_text_to_id(self):
        self.assertEqual(
            self.reversed_choice_field.to_internal_value('foo11'),
            TestChoices.foo.id,
        )

    def test_to_internal_value_with_choice_not_found_should_raise_validation_error(self):  # noqa
        with self.assertRaises(ValidationError):
            self.reversed_choice_field.to_internal_value('foo33')


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
