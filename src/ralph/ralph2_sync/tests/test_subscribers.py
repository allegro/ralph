from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.assets.models import AssetModel
from ralph.data_importer.models import ImportedObjects
from ralph.ralph2_sync.subscribers import ralph2_sync_ack


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
