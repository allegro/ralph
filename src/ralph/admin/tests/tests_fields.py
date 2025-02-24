# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ralph.admin.fields import MultilineField, MultivalueFormMixin
from ralph.tests.models import TestAsset


class SimpleTestForm(MultivalueFormMixin, forms.Form):
    multivalue_fields = ["sn", "barcode", "niw"]
    sn = MultilineField()
    barcode = MultilineField()
    niw = MultilineField(required=False)


class OneRequiredTestForm(MultivalueFormMixin, forms.Form):
    one_of_mulitvalue_required = ["sn", "barcode"]
    multivalue_fields = ["sn", "barcode"]
    sn = MultilineField()
    barcode = MultilineField()


class TestAssetForm(MultivalueFormMixin, forms.ModelForm):
    multivalue_fields = ["sn", "barcode"]
    one_of_mulitvalue_required = ["sn", "barcode"]
    sn = MultilineField("sn")
    barcode = MultilineField("barcode")

    class Meta:
        model = TestAsset
        fields = ["hostname", "sn", "barcode"]


class MultiValueFormTest(SimpleTestCase):
    def test_extend_empty_fields_at_the_end(self):
        data = {
            "sn": ["1", "2", "3"],
            "barcode": ["1"],
        }
        form = SimpleTestForm({})
        result = form.extend_empty_fields_at_the_end(data)
        self.assertEqual(
            result,
            {
                "sn": ["1", "2", "3"],
                "barcode": ["1", "", ""],
                "niw": ["", "", ""],
            },
        )

    def test_extend_empty_fields_at_the_end_with_empty_row(self):
        data = {
            "sn": ["1", "2", "3", ""],
            "barcode": ["1", "", "", ""],
        }
        form = SimpleTestForm({})
        result = form.extend_empty_fields_at_the_end(data)
        self.assertEqual(
            result,
            {
                "sn": ["1", "2", "3"],
                "barcode": ["1", "", ""],
                "niw": ["", "", ""],
            },
        )

    def test_works_for_single_value_each(self):
        data = {
            "sn": "sn1",
            "barcode": "bc1",
            "niw": "niw1",
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())

    def test_works_for_multi_value_each(self):
        data = {
            "sn": "sn1, sn2, sn3",
            "barcode": "bc1, bc2, bc3",
            "niw": "niw1, niw2, niw3",
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())

    def test_works_for_multi_value_with_empty_holes(self):
        data = {
            "sn": "sn1, sn2, sn3",
            "barcode": "bc1, bc2, bc3",
            "niw": "niw1, , niw3",
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["niw"], ["niw1", "", "niw3"])

    def test_works_for_multi_value_with_empty_holes_at_the_end(self):
        data = {
            "sn": "sn1, sn2, sn3",
            "barcode": "bc1, bc2, bc3",
            "niw": "niw1, ,",
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["niw"], ["niw1", "", ""])

    def test_works_for_multi_value_with_extension_to_longest_field(self):
        data = {
            "sn": "sn1, sn2, sn3",
            "barcode": "bc1, bc2, bc3",
            "niw": "niw1",
        }
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["niw"], ["niw1", "", ""])

    def test_valid_when_different_count(self):
        data = {"sn": "sn1", "barcode": "bc1, bc2", "niw": "niw1, niw2"}
        form = SimpleTestForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["sn"], ["sn1", ""])

    def test_not_valid_when_empty_multivalues(self):
        data = {
            "sn": "",
            "barcode": "",
        }
        form = OneRequiredTestForm(data)
        self.assertFalse(form.is_valid())

    def test_not_valid_when_none_multivalue_passed(self):
        data = {
            "sn": "sn1,,sn3",
            "barcode": "br1,,br3",
        }
        form = OneRequiredTestForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("sn", form.errors)
        self.assertIn("barcode", form.errors)


class MultilineFieldTest(SimpleTestCase):
    def test_field_works_for_single_value(self):
        field = MultilineField()
        value_with_duplicates = "1"
        self.assertEqual(field.clean(value_with_duplicates), ["1"])

    def test_field_works_for_multi_value(self):
        field = MultilineField()
        value_with_duplicates = "1,2"
        self.assertEqual(field.clean(value_with_duplicates), ["1", "2"])

    def test_field_not_valid_when_duplicates(self):
        field = MultilineField(allow_duplicates=False)
        value_with_duplicates = "1,1"
        with self.assertRaises(ValidationError):
            field.clean(value_with_duplicates)

    def test_field_valid_when_duplicates_allowed(self):
        field = MultilineField(allow_duplicates=True)
        value_with_duplicates = "1,1"
        self.assertEqual(field.clean(value_with_duplicates), ["1", "1"])

    def test_field_strips_whitespaces(self):
        field = MultilineField(allow_duplicates=True)
        value_with_duplicates = " 1 "
        self.assertEqual(field.clean(value_with_duplicates), ["1"])

    def test_field_allows_blank_elements(self):
        field = MultilineField(allow_duplicates=True)
        value_with_empty = "1,,3"
        self.assertEqual(field.clean(value_with_empty), ["1", "", "3"])
