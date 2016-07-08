from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings

from ralph.accounts.tests.factories import TeamFactory
from ralph.assets.models import (
    AssetModel,
    ConfigurationClass,
    ConfigurationModule
)
from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    ConfigurationModuleFactory,
    EnvironmentFactory,
    ServiceEnvironmentFactory,
    ServiceFactory
)
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldTypes
from ralph.networks.tests.factories import IPAddressFactory
from ralph.ralph2_sync.subscribers import (
    ralph2_sync_ack,
    sync_custom_fields_to_ralph3,
    sync_device_to_ralph3,
    sync_venture_role_to_ralph3,
    sync_venture_to_ralph3,
    sync_virtual_server_to_ralph3
)
from ralph.virtual.models import VirtualServer, VirtualServerType
from ralph.virtual.tests.factories import VirtualServerFactory


def _create_imported_object(factory, old_id, factory_kwargs=None):
    if factory_kwargs is None:
        factory_kwargs = {}
    obj = factory(**factory_kwargs)
    ImportedObjects.create(obj, old_id)
    return obj


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
            'custom_fields': custom_fields
        }
        sync_device_to_ralph3(data)
        self.assertEqual(dca.custom_fields_as_dict, custom_fields)

    def test_sync_device_new_management_ip(self):
        old_id = 1
        dca = DataCenterAssetFactory()
        ImportedObjects.create(obj=dca, old_pk=old_id)
        data = {
            'id': old_id,
            'management_ip': '10.20.30.40',
        }
        sync_device_to_ralph3(data)
        self.assertEqual(dca.management_ip, '10.20.30.40')

    def test_sync_device_existing_management_ip(self):
        old_id = 1
        ip = IPAddressFactory(address='10.20.30.40', is_management=True)
        dca = DataCenterAssetFactory()
        ImportedObjects.create(obj=dca, old_pk=old_id)
        data = {
            'id': old_id,
            'management_ip': '10.20.30.40',
        }
        sync_device_to_ralph3(data)
        self.assertEqual(dca.management_ip, '10.20.30.40')
        ip.refresh_from_db()
        ip.ethernet.refresh_from_db()
        self.assertEqual(ip.ethernet.base_object.pk, dca.pk)

    def test_sync_device_empty_venture_role(self):
        old_id = 1
        conf_class = ConfigurationClassFactory()
        dca = DataCenterAssetFactory(configuration_path=conf_class)
        ImportedObjects.create(obj=dca, old_pk=old_id)
        data = {
            'id': old_id,
            'venture_role': None,
        }
        sync_device_to_ralph3(data)
        dca.refresh_from_db()
        self.assertIsNone(dca.configuration_path)


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


class Ralph2SyncVirtualServerTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': 1,
            'type': 'unknown',
            'hostname': None,
            'sn': None,
            'service': None,
            'environment': None,
            'venture_role': None,
            'parent_id': None,
            'custom_fields': {}
        }

    def sync(self):
        obj = self._create_imported_virtual_server()
        sync_virtual_server_to_ralph3(self.data)
        obj.refresh_from_db()
        return obj

    def _create_imported_virtual_server(self, old_id=None):
        return _create_imported_object(
            factory=VirtualServerFactory,
            old_id=old_id if old_id else self.data['id']
        )

    def test_new_virtual_server_should_create_imported_object(self):
        self.assertEqual(VirtualServer.objects.count(), 0)
        sync_virtual_server_to_ralph3(self.data)
        self.assertEqual(VirtualServer.objects.count(), 1)
        vs = ImportedObjects.get_object_from_old_pk(
            VirtualServer, self.data['id']
        )
        self.assertEqual(vs.hostname, self.data['hostname'])

    def test_existing_virtual_server_should_updated(self):
        vs = self._create_imported_virtual_server()
        sync_virtual_server_to_ralph3(self.data)
        self.assertEqual(VirtualServer.objects.count(), 1)
        vs = ImportedObjects.get_object_from_old_pk(
            VirtualServer, self.data['id']
        )
        self.assertEqual(vs.hostname, self.data['hostname'])

    def test_sync_should_change_hostname(self):
        vs = self._create_imported_virtual_server()
        self.data['hostname'] = 'new.hostname.dc.net'
        self.assertNotEqual(self.data['hostname'], vs.hostname)
        sync_virtual_server_to_ralph3(self.data)
        vs.refresh_from_db()
        self.assertEqual(vs.hostname, self.data['hostname'])

    def test_sync_should_change_sn(self):
        vs = self._create_imported_virtual_server()
        self.data['sn'] = 'sn-123'
        self.assertNotEqual(self.data['sn'], vs.sn)
        sync_virtual_server_to_ralph3(self.data)
        vs.refresh_from_db()
        self.assertEqual(vs.sn, self.data['sn'])

    def test_sync_should_create_type_if_not_exist(self):
        self.data['type'] = 'new unique type'
        type_exists = VirtualServerType.objects.filter(name=self.data['type']).exists  # noqa
        self.assertFalse(type_exists())
        sync_virtual_server_to_ralph3(self.data)
        self.assertTrue(type_exists())

    @override_settings(
        RALPH2_RALPH3_VIRTUAL_SERVER_TYPE_MAPPING={
            'type in R2': 'type in R3'
        },
    )
    def test_sync_should_create_type_and_mapping(self):
        self.data['type'] = 'type in R2'
        type_exists = VirtualServerType.objects.filter(name='type in R3').exists  # noqa
        self.assertFalse(type_exists())
        sync_virtual_server_to_ralph3(self.data)
        self.assertTrue(type_exists())

    def test_sync_should_change_service_env(self):
        self.data['service'] = '123'
        service = _create_imported_object(
            ServiceFactory, self.data['service'], factory_kwargs={
                'uid': self.data['service']
            }
        )
        self.data['environment'] = '124'
        env = _create_imported_object(
            EnvironmentFactory, self.data['environment']
        )
        se = ServiceEnvironmentFactory(service=service, environment=env)
        vs = self.sync()
        self.assertEqual(vs.service_env, se)

    def test_sync_should_change_configuration_path(self):
        self.data['venture_role'] = 'venture_role_123'
        conf_class = _create_imported_object(
            ConfigurationClassFactory, self.data['venture_role']
        )
        vs = self.sync()
        self.assertEqual(vs.configuration_path, conf_class)

    def test_sync_should_change_parent(self):
        self.data['parent_id'] = '123333'
        parent = _create_imported_object(
            DataCenterAssetFactory, self.data['parent_id']
        )
        vs = self.sync()
        self.assertEqual(vs.parent.id, parent.id)

    def test_sync_should_change_custom_fields(self):
        cf = CustomField.objects.create(
            name='test_str', type=CustomFieldTypes.STRING,
        )
        custom_fields = {
            cf.name: 'test'
        }
        self.data['custom_fields'] = custom_fields
        vs = self.sync()
        self.assertEqual(vs.custom_fields_as_dict, custom_fields)
