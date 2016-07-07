from django.test import TestCase
from django.test.utils import override_settings


from ralph.business.models import (
    Department,
    Venture,
    VentureRole,
    RoleProperty,
    RolePropertyType,
    RolePropertyTypeValue,
    RolePropertyValue
)
from ralph.cmdb.tests.utils import (
    DeviceEnvironmentFactory,
    ServiceCatalogFactory
)
from ralph.discovery.models import (
    Device,
    DeviceModel,
    DeviceType,
)
from ralph.discovery.tests.util import DeviceFactory
from ralph.export_to_ng.subscribers import (
    sync_dc_asset_to_ralph2_handler,
    sync_venture_role_to_ralph2,
    sync_venture_to_ralph2,
    sync_virtual_server_to_ralph2
)
from ralph.util.tests.utils import VentureFactory, VentureRoleFactory
from ralph_assets.tests.utils.assets import DCAssetFactory


class DeviceDCAssetTestCase(TestCase):
    def setUp(self):
        self.data = {
            'ralph2_id': None,
            'service': None,
            'environment': None,
            'force_depreciation': 0,
            'data_center': None,
            'server_room': None,
            'rack': None,
            'id': 1,
            'orientation': 1,
            'position': 1,
            'sn': None,
            'barcode': None,
            'slot_no': 1,
            'price': 1,
            'niw': None,
            'task_url': 'http://tasks.local.net/issue-123',
            'remarks': 'empty',
            'order_no': 1,
            'invoice_date': None,
            'invoice_no': None,
            'provider': None,
            'source': None,
            'status': 1,
            'depreciation_rate': 48,
            'depreciation_end_date': None,
            'management_ip': None,
            'management_hostname': None,
            'hostname': 'test.local.net',
            'model': None,
            'property_of': None,
        }

    def sync(self, obj):
        sync_dc_asset_to_ralph2_handler(self.data)
        new_obj = obj.__class__.objects.get(id=obj.id)
        return new_obj

    def create_test_device(self):
        device = DeviceFactory()
        asset = DCAssetFactory()
        asset.device_info.ralph_device = device
        asset.device_info.save()
        self.data['ralph2_id'] = asset.id
        self.data['service'] = device.service.uid
        self.data['environment'] = device.device_environment.id
        self.data['rack'] = asset.device_info.rack_id
        self.data['data_center'] = asset.device_info.rack.data_center_id
        self.data['server_room'] = asset.device_info.rack.server_room_id
        self.data['model'] = asset.model_id
        self.data['sn'] = asset.sn
        self.data['barcode'] = asset.barcode
        self.data['invoice_date'] = asset.invoice_date.strftime('%d.%m.%Y')
        self.data['invoice_no'] = asset.invoice_no
        self.data['provider'] = asset.provider
        self.data['source'] = asset.source
        return device

    def _custom_fields_test_common(
        self, symbol='test_field', original_value='original_value',
        test_value='test_value', custom_fields=None, create_role_property=True,
        create_role_property_value=True, choices=None
    ):
        device = self.create_test_device()
        role_property = None
        if create_role_property:
            role_property = RoleProperty.objects.create(symbol=symbol)
        if choices:
            role_property_type = RolePropertyType.objects.create(
                symbol='choices type'
            )
            role_property.type = role_property_type
            role_property.save()
            for choice in choices:
                RolePropertyTypeValue.objects.create(
                    type=role_property_type, value=choice
                )
        if create_role_property and create_role_property_value:
            RolePropertyValue.objects.create(
                device=device, property=role_property, value=original_value
            )
        if custom_fields is None:
            custom_fields = {
                symbol: test_value
            }
        self.data['custom_fields'] = custom_fields
        return device, role_property

    @override_settings(RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_field'])
    def test_sync_should_update_custom_fields(self):
        device, _ = self._custom_fields_test_common()
        device = self.sync(device)
        self.assertEqual(
            device.get_property_set(),
            self.data['custom_fields']
        )

    @override_settings(RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=[])
    def test_sync_should_respect_whitelist(self):
        symbol = 'blacklisted_field'
        original_value = 'fo bar'
        device, _ = self._custom_fields_test_common(
            symbol=symbol, original_value=original_value
        )
        device = self.sync(device)
        self.assertEqual(
            device.get_property_set()[symbol],
            original_value
        )

    @override_settings(RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_field'])
    def test_sync_should_do_nothing_when_role_property_doesnt_exist(self):
        device, _ = self._custom_fields_test_common(create_role_property=False)
        device = self.sync(device)
        self.assertEqual(device.get_property_set(), {})

    @override_settings(RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_field'])
    def test_sync_should_do_nothing_when_role_property_value_doesnt_exist(self):  # noqa
        device, _ = self._custom_fields_test_common(create_role_property_value=False)  # noqa
        device = self.sync(device)
        self.assertEqual(device.get_property_set(), {})

    @override_settings(RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_field'])
    def test_sync_should_create_choice_to_type(self):  # noqa
        predefinied_choices = ['one', 'two', 'three']
        test_value = 'four'
        device, prop = self._custom_fields_test_common(
            original_value=predefinied_choices[0],
            choices=predefinied_choices,
            test_value=test_value
        )
        device = self.sync(device)
        self.assertEqual(device.get_property_set(), self.data['custom_fields'])
        self.assertTrue(
            RolePropertyTypeValue.objects.filter(
                type=prop.type, value=test_value
            ).exists()
        )


class SyncVentureTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': None,
            'ralph2_id': None,
            'ralph2_parent_id': None,
            'symbol': 'test',
            'department': None
        }

    def sync(self, obj):
        sync_venture_to_ralph2(self.data)
        new_obj = obj.__class__.objects.get(id=obj.id)
        return new_obj

    def test_sync_should_create_new_if_venture_doesnt_exist(self):
        self.data['ralph2_id'] = None
        sync_venture_to_ralph2(self.data)
        self.assertTrue(
            Venture.objects.filter(symbol=self.data['symbol'], name=self.data['symbol']).exists()  # noqa
        )

    def test_sync_should_update_symbol_and_name(self):
        venture = Venture.objects.create(name='old_name', symbol='old_name')
        venture.save()
        self.data['ralph2_id'] = venture.id
        self.data['symbol'] = 'new_name'
        venture = self.sync(venture)
        self.assertEqual(self.data['symbol'], venture.name)
        self.assertEqual(self.data['symbol'], venture.symbol)

    def test_sync_should_update_department(self):
        department = Department.objects.create(name='test_department')
        new_department = Department.objects.create(name='new_department')
        venture = Venture.objects.create(
            name='old_name', symbol='old_name', department=department
        )
        venture.save()
        self.data['ralph2_id'] = venture.id
        self.data['department'] = new_department.name
        venture = self.sync(venture)
        self.assertEqual(new_department, venture.department)

    def test_sync_should_update_parent(self):
        parent = Venture.objects.create(
            name='parent_name', symbol='parent_name'
        )
        venture = Venture.objects.create(
            name='old_name', symbol='old_name', parent=parent
        )
        new_parent = Venture.objects.create(
            name='new_parent_name', symbol='new_parent_name')
        self.data['ralph2_id'] = venture.id
        self.data['ralph2_parent_id'] = new_parent.id
        venture = self.sync(venture)
        self.assertEqual(new_parent, venture.parent)

    def test_sync_should_update_parent_if_parent_equal_none(self):
        parent = Venture.objects.create(
            name='parent_name', symbol='parent_name'
        )
        venture = Venture.objects.create(
            name='old_name', symbol='old_name', parent=parent
        )
        self.data['ralph2_id'] = venture.id
        self.data['ralph2_parent_id'] = None
        venture = self.sync(venture)
        self.assertEqual(None, venture.parent)

    def test_sync_should_keep_parent_if_not_present(self):
        parent = Venture.objects.create(
            name='parent_name', symbol='parent_name'
        )
        venture = Venture.objects.create(
            name='old_name', symbol='old_name', parent=parent
        )
        self.data['ralph2_id'] = venture.id
        del self.data['ralph2_parent_id']
        venture = self.sync(venture)
        self.assertEqual(parent, venture.parent)


class SyncVentureRoleTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': None,
            'ralph2_id': None,
            'ralph2_parent_id': None,
            'symbol': 'test',
        }

    def sync(self, obj):
        sync_venture_role_to_ralph2(self.data)
        new_obj = obj.__class__.objects.get(id=obj.id)
        return new_obj

    def test_sync_should_create_new_if_venture_role_doesnt_exist(self):
        venture = Venture.objects.create(name='name', symbol='name')
        self.data['ralph2_id'] = None
        self.data['ralph2_parent_id'] = venture.id
        sync_venture_role_to_ralph2(self.data)
        self.assertTrue(
            VentureRole.objects.filter(name=self.data['symbol']).exists()
        )

    def test_sync_should_update_venture(self):
        venture = Venture.objects.create(name='name', symbol='name')
        new_venture = Venture.objects.create(name='new_name', symbol='new_name')  # noqa
        venture_role = VentureRole.objects.create(
            name='test_name', venture=venture
        )
        self.data['ralph2_id'] = venture_role.id
        self.data['ralph2_parent_id'] = new_venture.id
        venture_role = self.sync(venture_role)
        self.assertEqual(new_venture, venture_role.venture)


class VirtualServerTestCase(TestCase):
    def setUp(self):
        self.data = {
            'id': None,
            'ralph2_id': None,
            'ralph2_parent_id': None,
            'hostname': 'test.dc.net',
            'sn': '21334',
            'type': 'XEN',
            'service_uid': None,
            'environment_id': None,
            'venture_id': None,
            'venture_role_id': None,
        }

    def create_test_virtual_server(self):
        model = DeviceModel.objects.create(
            name='XEN', type=DeviceType.virtual_server
        )
        return Device.objects.create(model=model)

    def sync(self, obj):
        sync_virtual_server_to_ralph2(self.data)
        new_obj = obj.__class__.objects.get(id=obj.id)
        return new_obj

    def test_sync_should_create_new_if_virtual_server_doesnt_exist(self):
        sync_virtual_server_to_ralph2(self.data)
        self.assertTrue(Device.objects.filter(sn=self.data['sn']).exists())

    def test_sync_should_update_name(self):
        device = self.create_test_virtual_server()
        self.data['ralph2_id'] = device.id
        self.data['hostname'] = 'new.dc.net'
        vs = self.sync(device)
        self.assertEqual(vs.name, self.data['hostname'])

    def test_sync_should_update_sn(self):
        device = self.create_test_virtual_server()
        self.data['ralph2_id'] = device.id
        self.data['sn'] = 'new-sn-22324234'
        vs = self.sync(device)
        self.assertEqual(vs.sn, self.data['sn'])

    def test_sync_should_create_model_if_doesnt_exist(self):
        device = self.create_test_virtual_server()
        old_count = DeviceModel.objects.count()
        self.data['ralph2_id'] = device.id
        self.data['type'] = 'new-unique-model'
        vs = self.sync(device)
        self.assertEqual(old_count + 1, DeviceModel.objects.count())
        self.assertEqual(
            vs.model, DeviceModel.objects.get(name=self.data['type'])
        )

    def test_sync_should_update_model(self):
        model = DeviceModel.objects.create(
            name='QEMU', type=DeviceType.virtual_server
        )
        device = self.create_test_virtual_server()
        old_count = DeviceModel.objects.count()
        self.data['ralph2_id'] = device.id
        self.data['type'] = model.name
        vs = self.sync(device)
        self.assertEqual(old_count, DeviceModel.objects.count())
        self.assertEqual(
            vs.model, DeviceModel.objects.get(name=self.data['type'])
        )

    def test_sync_should_update_service_env(self):
        new_service = ServiceCatalogFactory()
        new_env = DeviceEnvironmentFactory()
        device = self.create_test_virtual_server()
        device.service = ServiceCatalogFactory()
        device.device_environment = DeviceEnvironmentFactory()
        device.save()
        self.data['ralph2_id'] = device.id
        self.data['service_uid'] = new_service.uid
        self.data['environment_id'] = new_env.id
        vs = self.sync(device)
        self.assertEqual(vs.service, new_service)
        self.assertEqual(vs.device_environment, new_env)

    def test_sync_should_clear_service_env_when_given_none(self):
        device = self.create_test_virtual_server()
        device.service = ServiceCatalogFactory()
        device.device_environment = DeviceEnvironmentFactory()
        device.save()
        self.data['ralph2_id'] = device.id
        self.data['service_uid'] = None
        self.data['environment_id'] = None
        vs = self.sync(device)
        self.assertEqual(vs.service, None)
        self.assertEqual(vs.device_environment, None)

    def test_sync_should_update_venture_and_role(self):
        new_venture = VentureFactory()
        new_venture_role = VentureRoleFactory()
        device = self.create_test_virtual_server()
        device.venture = VentureFactory()
        device.venture_role = VentureRoleFactory()
        device.save()
        self.data['ralph2_id'] = device.id
        self.data['venture_id'] = new_venture.id
        self.data['venture_role_id'] = new_venture_role.id
        vs = self.sync(device)
        self.assertEqual(vs.venture, new_venture)
        self.assertEqual(vs.venture_role, new_venture_role)

    def test_sync_should_clear_venture_and_role_when_given_none(self):
        device = self.create_test_virtual_server()
        device.venture = VentureFactory()
        device.venture_role = VentureRoleFactory()
        device.save()
        self.data['ralph2_id'] = device.id
        self.data['venture_id'] = None
        self.data['venture_role_id'] = None
        vs = self.sync(device)
        self.assertEqual(vs.venture, None)
        self.assertEqual(vs.venture_role, None)
