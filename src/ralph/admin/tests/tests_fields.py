# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ralph.admin.fields import MultilineField, MultivalueFormMixin
from ralph.tests.models import TestAsset


class SimpleTestForm(MultivalueFormMixin, forms.Form):
    multivalue_fields = ['sn', 'barcode']
    sn = MultilineField()
    barcode = MultilineField()


class OneRequiredTestForm(MultivalueFormMixin, forms.Form):
    one_of_mulitvalue_required = ['sn', 'barcode']
    multivalue_fields = ['sn', 'barcode']
    sn = MultilineField()
    barcode = MultilineField()


class TestAssetForm(MultivalueFormMixin, forms.ModelForm):
    multivalue_fields = ['sn', 'barcode']
    one_of_mulitvalue_required = ['sn', 'barcode']
    sn = MultilineField('sn')
    barcode = MultilineField('barcode')

    class Meta:
        model = TestAsset
        fields = ['hostname', 'sn', 'barcode']


class MultiValueFormTest(SimpleTestCase):
    def test_works_for_single_value_each(self):
        data = {
            'sn': 'sn1',
            'barcode': 'bc1',
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())

    def test_works_for_multi_value_each(self):
        data = {
            'sn': 'sn1, sn2, sn3',
            'barcode': 'bc1, bc2, bc3',
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())

    def test_not_valid_when_different_count(self):
        data = {
            'sn': 'sn1',
            'barcode': 'bc1, bc2',
        }
        form = SimpleTestForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('sn', form.errors)
        self.assertIn('barcode', form.errors)

    def test_not_valid_when_empty_multivalues(self):
        data = {
            'sn': '',
            'barcode': '',
        }
        form = OneRequiredTestForm(data)
        self.assertFalse(form.is_valid())

    def test_not_valid_when_none_multivalue_passed(self):
        data = {
            'sn': 'sn1,,sn3',
            'barcode': 'br1,,br3',
        }
        form = OneRequiredTestForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('sn', form.errors)
        self.assertIn('barcode', form.errors)


class MultilineFieldTest(SimpleTestCase):
    def test_field_works_for_single_value(self):
        field = MultilineField()
        value_with_duplicates = '1'
        self.assertEqual(field.clean(value_with_duplicates), ['1'])

    def test_field_works_for_multi_value(self):
        field = MultilineField()
        value_with_duplicates = '1,2'
        self.assertEqual(field.clean(value_with_duplicates), ['1', '2'])

    def test_field_not_valid_when_duplicates(self):
        field = MultilineField(allow_duplicates=False)
        value_with_duplicates = '1,1'
        with self.assertRaises(ValidationError):
            field.clean(value_with_duplicates)

    def test_field_valid_when_duplicates_allowed(self):
        field = MultilineField(allow_duplicates=True)
        value_with_duplicates = '1,1'
        self.assertEqual(field.clean(value_with_duplicates), ['1', '1'])

    def test_field_strips_whitespaces(self):
        field = MultilineField(allow_duplicates=True)
        value_with_duplicates = ' 1 '
        self.assertEqual(field.clean(value_with_duplicates), ['1'])

    def test_field_allows_blank_elements(self):
        field = MultilineField(allow_duplicates=True)
        value_with_empty = '1,,3'
        self.assertEqual(field.clean(value_with_empty), ['1', '', '3'])
