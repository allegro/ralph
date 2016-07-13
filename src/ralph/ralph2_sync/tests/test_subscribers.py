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
from ralph.data_center.models import Cluster
from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFactory,
    DataCenterFactory
)
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldTypes
from ralph.networks.models import (
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)
from ralph.networks.tests.factories import (
    IPAddressFactory,
    NetworkEnvironmentFactory,
    NetworkFactory,
    NetworkKindFactory
)
from ralph.ralph2_sync.subscribers import (
    _get_obj,
    ralph2_sync_ack,
    sync_custom_fields_to_ralph3,
    sync_device_to_ralph3,
    sync_network_environment_to_ralph3,
    sync_network_kind_to_ralph3,
    sync_network_to_ralph3,
    sync_stacked_switch_to_ralph3,
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
            'management_ip': '10.20.30.40'
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
            'management_ip': '10.20.30.40'
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


class Ralph2NetworkTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': 1,
            'name': 'net-test',
            'address': '192.168.1.0/24',
            'remarks': 'remarks',
            'vlan': 1,
            'dhcp_broadcast': True,
            'gateway': '192.168.1.1',
            'reserved_ips': ['192.168.1.2', '192.168.1.2'],
            'environment_id': 1,
            'kind_id': 1,
            'racks_ids': [],
            'dns_servers': [],
        }

    def test_sync_sholud_create_new_network(self):
        sync_network_to_ralph3(self.data)
        net = ImportedObjects.get_object_from_old_pk(Network, self.data['id'])
        self.assertEqual(net.name, self.data['name'])

    def test_sync_should_create_gateway(self):
        sync_network_to_ralph3(self.data)
        self.assertTrue(
            IPAddress.objects.get(address=self.data['gateway'])
        )

    def test_sync_should_update_gateway(self):
        net = sync_network_to_ralph3(self.data)
        IPAddressFactory(network=net, address='192.168.1.10', is_gateway=True)
        sync_network_to_ralph3(self.data)
        self.assertTrue(
            IPAddress.objects.filter(address=self.data['gateway']).exists()
        )

    def test_sync_should_update_gateway_when_ip_already_exist_outside_net(self):
        net2 = NetworkFactory(address='192.168.0.0/15')
        IPAddressFactory(address='192.168.1.1', network=net2)
        sync_network_to_ralph3(self.data)
        net = ImportedObjects.get_object_from_old_pk(Network, self.data['id'])
        self.assertEqual(str(net.gateway), '192.168.1.1')

    def test_sync_should_delete_current_gateway(self):
        net = sync_network_to_ralph3(self.data)
        IPAddressFactory(network=net, address='192.168.1.10', is_gateway=True)
        self.data['gateway'] = None
        sync_network_to_ralph3(self.data)
        self.assertFalse(
            IPAddress.objects.filter(is_gateway=True).exists()
        )
        self.assertFalse(
            IPAddress.objects.filter(address='192.168.1.10').exists()
        )


class Ralph2NetworkKindTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': 1,
            'name': 'net-kind-test',
        }

    def _create_imported_network_kind(self, old_id=None):
        return _create_imported_object(
            factory=NetworkKindFactory,
            old_id=old_id if old_id else self.data['id']
        )

    def sync(self):
        obj = self._create_imported_network_kind()
        sync_network_kind_to_ralph3(self.data)
        obj.refresh_from_db()
        return obj

    def test_sync_should_create_new_network_kind(self):
        self.assertFalse(
            NetworkKind.objects.filter(name=self.data['name']).exists()
        )
        self.sync()
        self.assertTrue(NetworkKind.objects.get(name=self.data['name']))

    def test_sync_should_update_name(self):
        net_kind = self._create_imported_network_kind()
        self.data['name'] = 'new_name'
        self.assertNotEqual(self.data['name'], net_kind.name)
        sync_network_kind_to_ralph3(self.data)
        net_kind.refresh_from_db()
        self.assertEqual(net_kind.name, self.data['name'])


class Ralph2NetworkEnvironmentTestCase(TestCase):
    def setUp(self):
        self.dc = _create_imported_object(
            factory=DataCenterFactory, old_id=10
        )
        self.data = {
            'id': 1,
            'name': 'net-env',
            'data_center_id': 10,
            'domain': 'foo.net',
            'remarks': '',
            'hostname_template_prefix': 's1',
            'hostname_template_counter_length': 4,
            'hostname_template_postfix': '.foo.net'
        }

    def _create_imported_network_environment(self, old_id=None):
        return _create_imported_object(
            factory=NetworkEnvironmentFactory,
            old_id=old_id if old_id else self.data['id']
        )

    def sync(self):
        obj = self._create_imported_network_environment()
        sync_network_environment_to_ralph3(self.data)
        obj.refresh_from_db()
        return obj

    def test_sync_should_create_new_network_environment(self):
        self.assertFalse(
            NetworkEnvironment.objects.filter(name=self.data['name']).exists()
        )
        self.sync()
        self.assertTrue(NetworkEnvironment.objects.get(name=self.data['name']))

    def test_sync_should_update_hostname_template_if_created(self):
        self.data['hostname_template_prefix'] = 'x1'
        self.data['hostname_template_counter_length'] = 5
        self.data['hostname_template_postfix'] = '.foo.bar.net'
        sync_network_environment_to_ralph3(self.data)
        net_kind, _ = _get_obj(NetworkEnvironment, self.data['id'])
        self.assertEqual(
            net_kind.hostname_template_prefix,
            self.data['hostname_template_prefix']
        )
        self.assertEqual(
            net_kind.hostname_template_counter_length,
            self.data['hostname_template_counter_length']
        )
        self.assertEqual(
            net_kind.hostname_template_postfix,
            self.data['hostname_template_postfix']
        )

    def test_sync_shouldnt_update_hostname_template_if_not_created(self):
        self.data['hostname_template_prefix'] = 'x1'
        self.data['hostname_template_counter_length'] = 5
        self.data['hostname_template_postfix'] = '.foo.bar.net'
        net_kind = self.sync()
        self.assertNotEqual(
            net_kind.hostname_template_prefix,
            self.data['hostname_template_prefix']
        )
        self.assertNotEqual(
            net_kind.hostname_template_counter_length,
            self.data['hostname_template_counter_length']
        )
        self.assertNotEqual(
            net_kind.hostname_template_postfix,
            self.data['hostname_template_postfix']
        )


class Ralph2StackedSwitchSyncTestCase(TestCase):
    def setUp(self):
        self.service = _create_imported_object(
            ServiceFactory, 123, factory_kwargs={'uid': 'sc-123'}
        )
        self.env = _create_imported_object(EnvironmentFactory, 321)
        self.se = ServiceEnvironmentFactory(
            service=self.service, environment=self.env
        )
        self.conf_class = _create_imported_object(
            ConfigurationClassFactory, 987
        )
        CustomField.objects.create(
            name='test_field', type=CustomFieldTypes.STRING,
        )
        self.child1 = _create_imported_object(DataCenterAssetFactory, 1111)
        self.child2 = _create_imported_object(DataCenterAssetFactory, 2222)
        self.data = {
            'id': 1,
            'type': 'juniper switch',
            'hostname': 'ss-1.mydc.net',
            'service': 'sc-123',
            'environment': 321,
            'venture_role': 987,
            'custom_fields': {'test_field': 'some_value'},
            'child_devices': [
                {'asset_id': 2222, 'is_master': True},
                {'asset_id': 1111, 'is_master': False},
            ]
        }

    def test_stacked_switch_subscriber_for_new_obj(self):
        sync_stacked_switch_to_ralph3(self.data)
        ss = ImportedObjects.get_object_from_old_pk(Cluster, self.data['id'])
        self.assertEqual(ss.hostname, self.data['hostname'])
        self.assertEqual(ss.type.name, self.data['type'])
        self.assertEqual(ss.service_env.service, self.service)
        self.assertEqual(ss.service_env.environment, self.env)
        self.assertEqual(ss.configuration_path, self.conf_class)
        self.assertEqual(ss.custom_fields_as_dict, self.data['custom_fields'])
        self.assertCountEqual(
            [self.child1, self.child2], list(ss.base_objects.all())
        )
        self.assertEqual(
            ss.baseobjectcluster_set.get(is_master=True).base_object.pk,
            self.child2.pk
        )

    def test_stacked_switch_subscriber_for_existing_obj(self):
        ss = _create_imported_object(
            factory=ClusterFactory, old_id=self.data['id'],
            factory_kwargs={'type__name': self.data['type']}
        )
        sync_stacked_switch_to_ralph3(self.data)
        ss.refresh_from_db()
        self.assertEqual(ss.hostname, self.data['hostname'])
        self.assertEqual(ss.type.name, self.data['type'])
        self.assertEqual(ss.service_env.service, self.service)
        self.assertEqual(ss.service_env.environment, self.env)
        self.assertEqual(ss.configuration_path, self.conf_class)
        self.assertEqual(ss.custom_fields_as_dict, self.data['custom_fields'])
        self.assertCountEqual(
            [self.child1, self.child2], list(ss.base_objects.all())
        )
        self.assertEqual(
            ss.baseobjectcluster_set.get(is_master=True).base_object.pk,
            self.child2.pk
        )
