# -*- coding: utf-8 -*-
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from .models import SomeModel
from ..models import CustomField, CustomFieldTypes, CustomFieldValue


class CustomFieldModelsTestCase(TestCase):
    def setUp(self):
        self.sm1 = SomeModel.objects.create(name='abc')
        self.sm2 = SomeModel.objects.create(name='def')

        self.custom_field_str = CustomField.objects.create(
            name='test_str', type=CustomFieldTypes.STRING,
        )
        self.custom_field_str_with_default = CustomField.objects.create(
            name='test_str_default', type=CustomFieldTypes.STRING,
            default_value='default'
        )
        self.custom_field_choices = CustomField.objects.create(
            name='test_choices', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn',
        )

    def test_get_form_field_with_default(self):
        form_field = self.custom_field_str_with_default.get_form_field()
        self.assertIsInstance(form_field, forms.CharField)
        self.assertEqual(form_field.initial, 'default')

    def test_get_form_field_choicefield(self):
        form_field = self.custom_field_choices.get_form_field()
        self.assertIsInstance(form_field, forms.ChoiceField)
        self.assertEqual(
            form_field.choices,
            [
                ('qwerty', 'qwerty'),
                ('asdfgh', 'asdfgh'),
                ('zxcvbn', 'zxcvbn'),
            ]
        )
