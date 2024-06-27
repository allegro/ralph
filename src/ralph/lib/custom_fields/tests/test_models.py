# -*- coding: utf-8 -*-
from django import forms
from django.test import TestCase

from ..models import CustomField, CustomFieldTypes, CustomFieldValue
from .admin import SomeModelAdmin
from .models import ModelA, ModelB, SomeModel


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

    def test_fields_as_dict_should_return_dict(self):
        self.assertIsInstance(self.sm1.custom_fields_as_dict, dict)

    def test_update_custom_field_should_add_value(self):
        field_name, field_value = 'test_choices', 'qwerty'
        self.assertEqual({}, self.sm1.custom_fields_as_dict)
        self.sm1.update_custom_field(name=field_name, value=field_value)
        self.assertEqual(
            {field_name: field_value}, self.sm1.custom_fields_as_dict
        )

    def test_update_custom_field_should_update_value(self):
        field_name, field_value = 'test_choices', 'qwerty'
        new_value = 'asdfgh'
        self.sm1.update_custom_field(name=field_name, value=field_value)
        self.sm1.update_custom_field(name=field_name, value=new_value)
        self.assertEqual(
            {field_name: new_value}, self.sm1.custom_fields_as_dict
        )

    def test_should_custom_fields_as_dict_run_1_query(self):
        self.sm1.update_custom_field(name='test_str', value='new_value')
        self.sm1.update_custom_field(name='test_choices', value='qwerty')
        with self.assertNumQueries(1):
            self.sm1.custom_fields_as_dict


class CustomFieldInheritanceModelsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.custom_field_str = CustomField.objects.create(
            name='test str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        cls.custom_field_str2 = CustomField.objects.create(
            name='test str 2', type=CustomFieldTypes.STRING, default_value='abc'
        )

    def setUp(self):
        self.a1 = ModelA.objects.create()
        self.b1 = ModelB.objects.create(a=self.a1)
        self.sm1 = SomeModel.objects.create(name='abc', b=self.b1)
        self.sm2 = SomeModel.objects.create(name='def')

        self.cfv1 = CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str,
            value='sample_value',
        )
        self.cfv2 = CustomFieldValue.objects.create(
            object=self.sm2,
            custom_field=self.custom_field_str2,
            value='qwerty',
        )
        self.cfv3 = CustomFieldValue.objects.create(
            object=self.a1,
            custom_field=self.custom_field_str2,
            value='sample_value2',
        )

    def test_inheritance_when_foreign_key_is_null(self):
        sm2_custom_fields = list(self.sm2.custom_fields.all())
        self.assertCountEqual([self.cfv2], sm2_custom_fields)

    def test_inheritance(self):
        sm1_custom_fields = list(self.sm1.custom_fields.all())
        self.assertCountEqual([self.cfv1, self.cfv3], sm1_custom_fields)

    def test_inheritance_with_overwriting(self):
        # self.sm1 overwrite custom field value for custom_field_str2
        cfv4 = CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str2,
            value='sample_value11',
        )
        sm1_custom_fields = list(self.sm1.custom_fields.all())
        self.assertCountEqual([self.cfv1, cfv4], sm1_custom_fields)

    def test_admin_get_custom_fields_values_result(self):
        custom_fields_values = SomeModelAdmin._get_custom_fields_values(
            self.sm1
        )
        self.assertEqual(custom_fields_values, [
            {
                'name': 'test str',
                'object': '-',
                'object_url': '',
                'value': 'sample_value'
            },
            {
                'name': 'test str 2',
                'object': f'model a: ModelA object ({self.a1.pk})',
                'object_url': self.a1.get_absolute_url(),
                'value': 'sample_value2'
            }
        ])

    def test_admin_get_custom_fields_values_result_when_cfv_is_inherited(self):
        CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str2,
            value='sample_value11',
        )
        custom_fields_values = SomeModelAdmin._get_custom_fields_values(
            self.sm1
        )
        self.assertEqual(custom_fields_values, [
            {
                'name': 'test str',
                'object': '-',
                'object_url': '',
                'value': 'sample_value'
            },
            {
                'name': 'test str 2',
                'object': '-',
                'object_url': '',
                'value': 'sample_value11'
            }
        ])

    def test_cleaning_children_custom_field_values(self):
        self.assertIn(
            self.cfv1, list(self.sm1.custom_fields.all())
        )
        self.a1.clear_children_custom_field_value(self.custom_field_str)
        self.assertNotIn(self.cfv1, self.sm1.custom_fields.all())

    def test_cleaning_children_custom_field_values_with_overwrite_from_ancestor(
        self
    ):
        cfv4 = CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str2,
            value='12345',
        )
        self.assertIn(cfv4, list(self.sm1.custom_fields.all()))
        self.a1.clear_children_custom_field_value(self.custom_field_str2)
        self.assertIn(self.cfv3, self.sm1.custom_fields.all())
        self.assertNotIn(cfv4, self.sm1.custom_fields.all())
