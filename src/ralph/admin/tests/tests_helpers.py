# -*- coding: utf-8 -*-
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase

from ralph.admin.helpers import get_field_by_relation_path
from ralph.assets.models.assets import Asset, Manufacturer


class ModelFieldsTestCase(TestCase):
    def test_return_ok_when_simply_field(self):
        field_name = 'barcode'
        found = get_field_by_relation_path(Asset, field_name)
        self.assertEqual(found, Asset._meta.get_field(field_name))

    def test_return_ok_when_long_path(self):
        found = get_field_by_relation_path(Asset, 'model__manufacturer__name')
        self.assertEqual(found, Manufacturer._meta.get_field('name'))

    def test_raise_exception_when_no_field(self):
        fake_field = 'device_info__fortunately_unexisting_deprecated_field'
        with self.assertRaises(FieldDoesNotExist):
            found = get_field_by_relation_path(Asset, fake_field)
