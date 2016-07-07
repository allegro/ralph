from django.test import TestCase
from django.test.utils import override_settings

from ralph.business.models import (
    Department,
    RoleProperty,
    RolePropertyType,
    RolePropertyTypeValue,
    RolePropertyValue,
    Venture,
    VentureRole,
)
from ralph.cmdb.tests.utils import (
    DeviceEnvironmentFactory,
    ServiceCatalogFactory
)
from ralph.discovery.models import DeviceType, Device
from ralph.export_to_ng.publishers import (
    sync_device_to_ralph3,
    sync_role_property_to_ralph3,
    sync_venture_role_to_ralph3,
    sync_venture_to_ralph3,
)
from ralph_assets.tests.utils.assets import DCAssetFactory


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_device_to_ralph3'],
    RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_symbol', 'test_symbol2'])
class DevicePublisherTestCase(TestCase):
    def setUp(self):
        self.asset = DCAssetFactory()
        self.device = self.asset.get_ralph_device()
        assert self.device is not None
        self.device.management_ip = ('mgmt-1.mydc.net', '10.20.30.40')
        self.device.name = 's1.mydc.net'
        self.device.service = ServiceCatalogFactory(
            name='service-1', uid='sc-1'
        )
        self.device.device_environment = DeviceEnvironmentFactory(
            id=9876, name='prod'
        )
        self.venture1 = Venture.objects.create(
            name='Venture 1', symbol='v1',
        )
        self.venture_role = VentureRole.objects.create(
            id=11111,
            name='abcd',
            venture=self.venture1
        )
        self.device.venture = self.venture1
        self.device.venture_role = self.venture_role

    @override_settings(RALPH3_HERMES_SYNC_ENABLED=False)
    def test_sync_device_when_hermes_sync_disabled(self):
        result = sync_device_to_ralph3(Device, self.device)
        self.assertIsNone(result)

    @override_settings(RALPH3_HERMES_SYNC_FUNCTIONS=[])
    def test_sync_device_when_func_disabled(self):
        result = sync_device_to_ralph3(Device, self.device)
        self.assertIsNone(result)

    def test_publish_device_without_asset(self):
        device_without_asset = Device.create(
            [('1', 'DEADBEEFCAFE', 0)],
            model_name='xxx',
            model_type=DeviceType.rack_server
        )
        result = sync_device_to_ralph3(Device, device_without_asset)
        self.assertEqual(result, {})

    def test_publish_device_simple(self):
        asset = DCAssetFactory()
        device = asset.get_ralph_device()
        device.name = 's2.mydc.net'
        device.service = None
        device.device_environment = None
        result = sync_device_to_ralph3(Device, device)
        self.assertEqual(result, {
            'id': asset.id,
            'hostname': 's2.mydc.net',
            'service': None,
            'environment': None,
            'management_ip': '',
            'management_hostname': '',
            'venture_role': None,
            'custom_fields': {},
        })

    def test_publish_device_full(self):
        result = sync_device_to_ralph3(Device, self.device)
        self.assertEqual(result, {
            'id': self.asset.id,
            'hostname': 's1.mydc.net',
            'service': 'sc-1',
            'environment': 9876,
            'management_ip': '10.20.30.40',
            'management_hostname': 'mgmt-1.mydc.net',
            'venture_role': 11111,
            'custom_fields': {},
        })

    def test_devices_properties(self):
        property_symbol = 'test_symbol'
        property_value = 'test_value'
        property_symbol2 = 'test_symbol2'
        self.device.venture_role.roleproperty_set.create(symbol=property_symbol)  # noqa
        prop2 = self.device.venture_role.roleproperty_set.create(
            symbol=property_symbol2
        )
        self.device.set_property(property_symbol, property_value, None)
        RolePropertyValue.objects.get_or_create(
            property=prop2, device=self.device, value=None
        )
        result = sync_device_to_ralph3(Device, self.device)
        self.assertEqual(result, {
            'id': self.asset.id,
            'hostname': 's1.mydc.net',
            'service': 'sc-1',
            'environment': 9876,
            'management_ip': '10.20.30.40',
            'management_hostname': 'mgmt-1.mydc.net',
            'venture_role': 11111,
            'custom_fields': {
                property_symbol: property_value,
                property_symbol2: '',
            },
        })


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_venture_to_ralph3'])
class VenturePublisherTestCase(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='TEAM1')
        self.venture1 = Venture.objects.create(
            name='Venture 1', symbol='v1',
        )
        self.venture2 = Venture.objects.create(
            name='Venture 2', symbol='v2', parent=self.venture1,
            department=self.department
        )

    def test_publish_venture_without_parent_and_team(self):
        result = sync_venture_to_ralph3(Venture, self.venture1)
        self.assertEqual(result, {
            'id': self.venture1.id,
            'symbol': 'v1',
            'department': None,
            'parent': None,
        })

    def test_publish_venture_with_parent_and_team(self):
        result = sync_venture_to_ralph3(Venture, self.venture2)
        self.assertEqual(result, {
            'id': self.venture2.id,
            'symbol': 'v2',
            'department': 'TEAM1',
            'parent': self.venture1.id,
        })


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_venture_role_to_ralph3'])
class VentureRolePublisherTestCase(TestCase):
    def setUp(self):
        self.venture1 = Venture.objects.create(
            name='Venture 1', symbol='v1',
        )
        self.venture_role = VentureRole.objects.create(
            name='abcd',
            venture=self.venture1
        )
        self.venture_role2 = VentureRole.objects.create(
            name='qwerty',
            venture=self.venture1,
            parent=self.venture_role
        )

    def test_publish_venture_role(self):
        result = sync_venture_role_to_ralph3(VentureRole, self.venture_role)
        self.assertEqual(result, {
            'id': self.venture_role.id,
            'name': 'abcd',
            'venture': self.venture1.id,
        })

    def test_publish_venture_role_with_parent(self):
        result = sync_venture_role_to_ralph3(VentureRole, self.venture_role2)
        self.assertEqual(result, {
            'id': self.venture_role2.id,
            'name': 'abcd__qwerty',
            'venture': self.venture1.id,
        })


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_role_property_to_ralph3'],
    RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_symbol'],)
class RolePropertyPublisherTestCase(TestCase):
    def setUp(self):
        self.prop = RoleProperty.objects.create(
            symbol='test_symbol', default='default_value'
        )

    def test_publish_role_property(self):
        result = sync_role_property_to_ralph3(RoleProperty, self.prop)
        self.assertEqual(result, {
            'symbol': self.prop.symbol,
            'default': self.prop.default,
            'choices': []
        })

    def test_publish_role_property_with_choices(self):
        choices = ['active', 'pending', 'finished']
        self.prop.type = RolePropertyType.objects.create(symbol='status')
        for choice in choices:
            RolePropertyTypeValue.objects.create(
                type=self.prop.type, value=choice
            )
        result = sync_role_property_to_ralph3(RoleProperty, self.prop)
        self.assertEqual(result, {
            'symbol': self.prop.symbol,
            'default': self.prop.default,
            'choices': choices
        })
