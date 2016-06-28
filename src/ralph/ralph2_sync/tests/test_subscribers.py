from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.accounts.tests.factories import TeamFactory
from ralph.assets.models import (
    AssetModel,
    ConfigurationClass,
    ConfigurationModule
)
from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    ConfigurationModuleFactory
)
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldTypes
from ralph.ralph2_sync.subscribers import (
    ralph2_sync_ack,
    sync_device_to_ralph3,
    sync_venture_role_to_ralph3,
    sync_venture_to_ralph3,
)


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


class Ralph2DataCenterAssetTestCase(TestCase):
    def test_sync_device_custom_fields(self):
        old_id = 1
        field_name = 'test_field'
        dca = DataCenterAssetFactory()
        CustomField.objects.create(name=field_name)
        ImportedObjects.create(obj=dca, old_pk=old_id)
        custom_fields = {field_name: 'test_value'}
        data = {
            'id': old_id,
            'hostname': 'test',
            'management_ip': None,
            'service': None,
            'environment': None,
            'custom_fields': custom_fields
        }
        sync_device_to_ralph3(data)
        self.assertEqual(dca.custom_fields_as_dict, custom_fields)


class Ralph2CustomFieldsTestCase(TestCase):
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


class Ralph2SyncVentureTestCase(TestCase):
    def setUp(self):
        self.conf_module = ConfigurationModuleFactory()
        ImportedObjects.create(self.conf_module, 11)
        self.team = TeamFactory(name='TEAM1')

    def test_new_venture_with_valid_team_without_parent(self):
        data = {
            'id': 1122,
            'symbol': 'v1',
            'department': 'TEAM1',
            'parent': None,
        }
        sync_venture_to_ralph3(data)
        conf_module = ImportedObjects.get_object_from_old_pk(
            ConfigurationModule, 1122
        )
        self.assertEqual(conf_module.name, 'v1')
        self.assertEqual(conf_module.support_team, self.team)
        self.assertIsNone(conf_module.parent)

    def test_new_venture_with_valid_team_with_parent(self):
        data = {
            'id': 1122,
            'symbol': 'v1',
            'department': None,
            'parent': 11,
        }
        sync_venture_to_ralph3(data)
        conf_module = ImportedObjects.get_object_from_old_pk(
            ConfigurationModule, 1122
        )
        self.assertEqual(conf_module.name, 'v1')
        self.assertIsNone(conf_module.support_team)
        self.assertEqual(conf_module.parent, self.conf_module)

    def test_update_existing_venture(self):
        data = {
            'id': 11,
            'symbol': 'v22',
            'department': 'TEAM1',
            'parent': None,
        }
        sync_venture_to_ralph3(data)
        self.conf_module.refresh_from_db()
        self.assertEqual(self.conf_module.name, 'v22')
        self.assertEqual(self.conf_module.support_team, self.team)
        self.assertIsNone(self.conf_module.parent)

    def test_venture_with_non_existing_parent(self):
        data = {
            'id': 33,
            'symbol': 'v22',
            'department': 'TEAM1',
            'parent': -1,
        }
        conf_modules_count = ConfigurationModule.objects.count()
        sync_venture_to_ralph3(data)
        # new conf module should not be added
        self.assertEqual(
            ConfigurationModule.objects.count(), conf_modules_count
        )
        with self.assertRaises(ImportedObjectDoesNotExist):
            ImportedObjects.get_object_from_old_pk(
                ConfigurationModule, 33
            )


class Ralph2SyncVentureRoleTestCase(TestCase):
    def setUp(self):
        self.conf_module = ConfigurationModuleFactory()
        ImportedObjects.create(self.conf_module, 11)
        self.conf_class = ConfigurationClassFactory()
        ImportedObjects.create(self.conf_class, 12)

    def test_new_venture_role(self):
        data = {
            'id': 1122,
            'name': 'v1',
            'venture': 11,
        }
        sync_venture_role_to_ralph3(data)
        conf_class = ImportedObjects.get_object_from_old_pk(
            ConfigurationClass, 1122
        )
        self.assertEqual(conf_class.class_name, 'v1')
        self.assertEqual(conf_class.module, self.conf_module)

    def test_update_existing_venture_role(self):
        data = {
            'id': 12,
            'name': 'v1',
            'venture': 11,
        }
        conf_classes_count = ConfigurationClass.objects.count()
        sync_venture_role_to_ralph3(data)
        self.assertEqual(
            ConfigurationClass.objects.count(), conf_classes_count
        )
        self.conf_class.refresh_from_db()
        self.assertEqual(self.conf_class.class_name, 'v1')
        self.assertEqual(self.conf_class.module, self.conf_module)

    def test_venture_role_with_non_existing_parent(self):
        data = {
            'id': 33,
            'name': 'v22',
            'venture': -1,
        }
        conf_classes_count = ConfigurationClass.objects.count()
        sync_venture_role_to_ralph3(data)
        self.assertEqual(
            ConfigurationClass.objects.count(), conf_classes_count
        )
        with self.assertRaises(ImportedObjectDoesNotExist):
            ImportedObjects.get_object_from_old_pk(
                ConfigurationModule, 33
            )
