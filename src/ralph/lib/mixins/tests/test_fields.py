# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from ralph.assets.models.base import BaseObject
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.fields import TaggitTagField
from ralph.lib.mixins.tests.models import MACModel
from ralph.tests.models import BaseObjectForeignKeyModel


class BaseObjectForeignKeyTestCase(TestCase):
    def test_limit_choices(self):
        model = BaseObjectForeignKeyModel.objects.create(
            base_object=BaseObject.objects.create()
        )
        bo_field = model._meta.get_field('base_object')
        content_types = ContentType.objects.get_for_models(
            BackOfficeAsset, DataCenterAsset
        )
        content_type_result = bo_field.limit_choices()['content_type__in']
        self.assertListEqual(
            [i.id for i in content_type_result],
            [i.id for i in content_types.values()]
        )


class TestTaggitTagField(TestCase):
    def setUp(self):
        self.field = TaggitTagField()

    def test_field_hasnt_changed(self):
        self.assertFalse(self.field.has_changed(['a', 'b'], 'a,b'))

    def test_field_hasnt_changed_with_space(self):
        self.assertFalse(self.field.has_changed(['a', 'b'], 'a, b'))

    def test_field_hasnt_changed_with_trailing_comma(self):
        self.assertFalse(self.field.has_changed(['a', 'b'], 'a, b, '))

    def test_field_hasnt_changed_different_order(self):
        self.assertFalse(self.field.has_changed(['a', 'b'], 'b, a'))

    def test_field_has_changed_new_item(self):
        self.assertTrue(self.field.has_changed(['a', 'b'], 'a, b, c'))

    def test_field_has_changed_new_item_different_order(self):
        self.assertTrue(self.field.has_changed(['a', 'b'], 'c, b, a'))

    def test_field_has_changed_remove_item(self):
        self.assertTrue(self.field.has_changed(['a', 'b'], 'a,'))

    def test_field_has_changed_remove_item_different_order(self):
        self.assertTrue(self.field.has_changed(['a', 'b', 'c'], 'c,a'))


class TestMACAddressField(TestCase):
    def test_mac_without_separators(self):
        instance = MACModel()
        instance.mac = 'aabbccddeeff'
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.mac, 'AA:BB:CC:DD:EE:FF')

    def test_mac_with_colon_separators(self):
        instance = MACModel()
        instance.mac = 'aa:00:BB:cc:99:55'
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.mac, 'AA:00:BB:CC:99:55')

    def test_mac_with_hyphen_separators(self):
        instance = MACModel()
        instance.mac = 'aa-00-BB-cc-99-55'
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.mac, 'AA:00:BB:CC:99:55')

    def test_mac_with_incomplete_octet(self):
        instance = MACModel()
        instance.mac = 'abbccddeeff'
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.mac, '0A:BB:CC:DD:EE:FF')

    def test_mac_with_invalid_mac(self):
        with self.assertRaises(ValueError):
            MACModel.objects.create(mac='xxxx')
