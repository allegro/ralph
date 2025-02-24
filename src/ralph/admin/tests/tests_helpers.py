# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase

from ralph.admin.helpers import (
    generate_html_link,
    get_content_type_for_model,
    get_field_by_relation_path,
    getattr_dunder
)
from ralph.assets.models.assets import Asset, Manufacturer
from ralph.assets.models.base import BaseObject


@ddt
class ModelFieldsTestCase(TestCase):
    def test_return_ok_when_simply_field(self):
        field_name = "barcode"
        found = get_field_by_relation_path(Asset, field_name)
        self.assertEqual(found, Asset._meta.get_field(field_name))

    def test_return_ok_when_long_path(self):
        found = get_field_by_relation_path(Asset, "model__manufacturer__name")
        self.assertEqual(found, Manufacturer._meta.get_field("name"))

    def test_raise_exception_when_no_field(self):
        fake_field = "device_info__fortunately_unexisting_deprecated_field"
        with self.assertRaises(FieldDoesNotExist):
            get_field_by_relation_path(Asset, fake_field)

    def test_getattr_dunder(self):
        """getattr_dunder works recursively"""

        class A:
            pass

        a = A()
        a.b = A()
        a.b.name = "spam"
        self.assertEqual(getattr_dunder(a, "b__name"), "spam")

    @unpack
    @data((BaseObject, Asset), (Manufacturer, Manufacturer))
    def test_get_content_type_for_model(self, expected_model, model):
        self.assertEqual(
            ContentType.objects.get_for_model(expected_model),
            get_content_type_for_model(model),
        )


class GenerateLinkTest(TestCase):
    def test_generate_html_link(self):
        url = generate_html_link(
            "http://test.com/",
            label="Name",
            params={"param": 1},
        )
        self.assertEqual(url, '<a href="http://test.com/?param=1">Name</a>')
