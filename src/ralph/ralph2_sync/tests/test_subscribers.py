from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.assets.models import AssetModel
from ralph.data_importer.models import ImportedObjects
from ralph.ralph2_sync.subscribers import (
    ralph2_sync_ack,
    sync_custom_fields_to_ralph3,
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldTypes


class Ralph2SyncACKTestCase(TestCase):
    def setUp(self):
        self.ct = ContentType.objects.get_for_model(AssetModel)

    def test_ack_when_entry_does_not_exist_before(self):
        old_count = ImportedObjects.objects.count()
        ralph2_sync_ack(
            data={'model': 'AssetModel', 'id': 123, 'ralph3_id': 321}
        )
        self.assertEqual(ImportedObjects.objects.count(), old_count + 1)
        io = ImportedObjects.objects.get(content_type=self.ct, object_pk='321')
        self.assertEqual(io.old_object_pk, '123')

    def test_ack_when_entry_exists_before(self):
        ImportedObjects.objects.create(
            content_type=self.ct,
            object_pk='321',
            old_object_pk='123',
        )
        old_count = ImportedObjects.objects.count()
        ralph2_sync_ack(
            data={'model': 'AssetModel', 'id': 123, 'ralph3_id': 321}
        )
        self.assertEqual(ImportedObjects.objects.count(), old_count)
        ImportedObjects.objects.get(
            content_type=ContentType.objects.get_for_model(AssetModel),
            object_pk='321'
        )


class CustomFieldsFromRalph2TestCase(TestCase):
    def test_sync_custom_fields_to_ralph3_with_choices(self):
        data = {
            'symbol': 'test_name',
            'default': '1',
            'choices': ['1', '2', '3']
        }
        sync_custom_fields_to_ralph3(data=data)
        cf = CustomField.objects.get(name=data['symbol'])
        self.assertEqual(cf._get_choices(), data['choices'])
        self.assertEqual(cf.default_value, data['default'])
        self.assertEqual(cf.type, CustomFieldTypes.CHOICE)

    def test_sync_custom_fields_to_ralph3_without_choices(self):
        data = {
            'symbol': 'test_name',
            'default': '1',
            'choices': []
        }
        sync_custom_fields_to_ralph3(data=data)
        cf = CustomField.objects.get(name=data['symbol'])
        self.assertEqual(cf.default_value, data['default'])
        self.assertEqual(cf.type, CustomFieldTypes.STRING)
