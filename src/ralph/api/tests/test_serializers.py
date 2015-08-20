# -*- coding: utf-8 -*-
from collections import OrderedDict

from dj.choices import Choices
from rest_framework.exceptions import ValidationError

from ralph.api.serializers import ReversedChoiceField
from ralph.tests import RalphTestCase


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
