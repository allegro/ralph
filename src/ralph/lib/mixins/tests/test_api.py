from django.test import TestCase
from rest_framework.exceptions import ValidationError

from ..api import ChoiceFieldWithOtherOptionField, OTHER


class TestChoiceFieldWithOtherOptionSerializer(TestCase):
    def setUp(self):
        self.choices = [
            ('poor', 'Poor quality'),
            ('medium', 'Medium quality'),
            ('good', 'Good quality'),
        ]
        self.field_with_auto = ChoiceFieldWithOtherOptionField(
            choices=self.choices,
            other_option_label='my_other_field',
            auto_other_choice=True,
        )
        self.field_without_auto = ChoiceFieldWithOtherOptionField(
            choices=self.choices,
            other_option_label='my_other_field',
            auto_other_choice=False,
        )

    def test_valid_choices_field_with_auto_should_contains_other(self):
        self.assertEqual(self.field_with_auto.choices[OTHER], 'my_other_field')

    def test_valid_choices_field_without_auto_should_not_contains_other(self):
        self.assertNotIn(OTHER, self.field_without_auto.choices)

    def test_to_internal_value_for_primitive_value(self):
        result = self.field_with_auto.run_validation('poor')
        self.assertEqual(result, {'value': 'poor'})

    def test_to_internal_value_for_primitive_value_invalid_value(self):
        with self.assertRaises(ValidationError):
            self.field_with_auto.run_validation('invalid')

    def test_to_internal_value_for_compound_value(self):
        result = self.field_with_auto.run_validation({'value': 'poor'})
        self.assertEqual(result, {'value': 'poor'})

    def test_to_internal_value_for_compound_value_other(self):
        result = self.field_with_auto.run_validation(
            {'value': '__other__', '__other__': 'other value'}
        )
        self.assertEqual(
            result, {'value': '__other__', '__other__': 'other value'}
        )

    def test_to_internal_value_for_compound_value_invalid_value(self):
        with self.assertRaises(ValidationError):
            self.field_with_auto.run_validation({'value': 'invalid'})
