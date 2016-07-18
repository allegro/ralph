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
from ralph.discovery.models import (
    DeviceType,
    Device,
    Network,
    NetworkTerminator
)
from ralph.discovery.tests.util import (
    DeprecatedRackFactory,
    DNSServerFactory,
    NetworkFactory,
    EnvironmentFactory,
    DeprecatedDataCenterFactory,
    DataCenterFactory as NetworkDataCenter
)
from ralph.export_to_ng.publishers import (
    sync_device_to_ralph3,
    sync_network_to_ralph3,
    sync_network_environment_to_ralph3,
    sync_role_property_to_ralph3,
    sync_stacked_switch_to_ralph3,
    sync_venture_role_to_ralph3,
    sync_venture_to_ralph3,
)
from ralph_assets.tests.utils.assets import (
    DCAssetFactory, DataCenterFactory, RackFactory
)
from ralph_assets.models_dc_assets import DeprecatedRalphDC


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_device_to_ralph3'],
    RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=[
        'test_symbol', 'test_symbol2', 'for_device_only'
    ]
)
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

        # this is property unrelated to current venture role of device
        # it might comes from some previous role of this device, but it's still
        # attached to this device in DB - but it's NOT visible in GUI or through
        # puppet-classifier endpoint, so we should not sync it as well
        venture_role2 = VentureRole.objects.create(
            name='qwerty', venture=self.venture1
        )
        property_for_device_only = venture_role2.roleproperty_set.create(
            symbol='for_device_only'
        )
        RolePropertyValue.objects.create(
            property=property_for_device_only,
            value='xxxxx',
            device=self.device
        )
        # it is, unfortunately, accessible through Device's get_property_set -_-
        self.assertIn('for_device_only', self.device.get_property_set())

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

        # if we change Device's venture_role to venture_role2, this field is
        # in dump to sync
        self.device.venture_role = venture_role2
        result2 = sync_device_to_ralph3(Device, self.device)
        self.assertIn('for_device_only', result2['custom_fields'])


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


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_network_to_ralph3'])
class NetworkPublisherTestCase(TestCase):
    def setUp(self):
        self.net = NetworkFactory(
            address='192.168.1.0/24',
            remarks='lorem ipsum dolor sit amet',
            vlan=10,
            dhcp_broadcast=True,
            gateway='192.168.1.1',
            reserved=0,
            reserved_top_margin=0,
        )

    def test_publish_network(self):
        self.assertEqual(sync_network_to_ralph3(Network, self.net), {
            'id': self.net.id,
            'name': self.net.name,
            'address': self.net.address,
            'remarks': self.net.remarks,
            'vlan': self.net.vlan,
            'dhcp_broadcast': self.net.dhcp_broadcast,
            'gateway': self.net.gateway,
            'reserved_ips': [],
            'environment_id': self.net.environment_id,
            'kind_id': self.net.kind_id,
            'racks_ids': [],
            'dns_servers': [],
            'terminators': [],
        })

    def test_reserved_ips(self):
        self.net.reserved = 1
        self.net.reserved_top_margin = 1
        self.net.save()
        self.assertEqual(
            sync_network_to_ralph3(Network, self.net)['reserved_ips'],
            ['192.168.1.1', '192.168.1.254']
        )

    def test_racks_ids(self):
        racks = [DeprecatedRackFactory() for _ in range(0, 5)]
        for rack in racks:
            RackFactory(deprecated_ralph_rack=rack)
        self.net.racks.add(*racks)
        self.net.save()
        self.assertEqual(
            sync_network_to_ralph3(Network, self.net)['racks_ids'],
            [rack.id for rack in racks]
        )

    def test_dns_servers(self):
        servers = [DNSServerFactory() for _ in range(0, 5)]
        self.net.custom_dns_servers.add(*servers)
        self.net.save()
        self.assertEqual(
            sync_network_to_ralph3(Network, self.net)['dns_servers'],
            [str(dns.ip_address) for dns in servers]
        )

    def test_terminators(self):
        asset = DCAssetFactory()
        device = asset.get_ralph_device()
        device.name = 'asset1.mydc.net'
        device.save()

        stacked_switch = Device.create(
            sn='11', model_name='Juniper stacked switch',
            model_type=DeviceType.switch_stack
        )
        stacked_switch.name = 'ss1.mydc.net'
        stacked_switch.save()

        self.net.terminators.add(
            NetworkTerminator.objects.create(name='asset1.mydc.net')
        )
        self.net.terminators.add(
            NetworkTerminator.objects.create(name='ss1.mydc.net')
        )
        self.net.terminators.add(
            NetworkTerminator.objects.create(name='unknown.mydc.net')
        )

        result = sync_network_to_ralph3(Network, self.net)
        self.assertItemsEqual(result['terminators'], [
            ('StackedSwitch', stacked_switch.id),
            ('DataCenterAsset', asset.id),
        ])


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_network_environment_to_ralph3'])
class NetworkEnvironmentPublisherTestCase(TestCase):
    def setUp(self):
        self.asset_dc = DataCenterFactory(
            name='DC#1',
        )
        self.env = EnvironmentFactory(
            domain='dc.net', data_center=NetworkDataCenter(name='DC#1'),
            hosts_naming_template='server<1000,5000>.dc.net'
        )

    def test_publish(self):
        self.assertEqual(
            sync_network_environment_to_ralph3(self.env.__class__, self.env),
            {
                'id': self.env.id,
                'name': self.env.name,
                'data_center_id': self.asset_dc.id,
                'domain': self.env.domain,
                'remarks': self.env.remarks,
                'hostname_template_counter_length': 3,
                'hostname_template_postfix': '.dc.net',
                'hostname_template_prefix': 'server1',
            }
        )

    def test_hostname_template(self):
        self.env.hosts_naming_template = '<10,99>.dc.net'
        self.env.save()
        self.assertEqual(
            sync_network_environment_to_ralph3(self.env.__class__, self.env),
            {
                'id': self.env.id,
                'name': self.env.name,
                'data_center_id': self.asset_dc.id,
                'domain': self.env.domain,
                'remarks': self.env.remarks,
                'hostname_template_counter_length': 1,
                'hostname_template_postfix': '.dc.net',
                'hostname_template_prefix': '1',
            }
        )


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_stacked_switch_to_ralph3'],
    RALPH2_HERMES_ROLE_PROPERTY_WHITELIST=['test_symbol']
)
class StackedSwitchPublisherTestCase(TestCase):
    def setUp(self):
        self.child1 = DCAssetFactory()
        self.child2 = DCAssetFactory()
        self.child1_device = self.child1.get_ralph_device()
        self.child2_device = self.child2.get_ralph_device()

        self.venture1 = Venture.objects.create(
            name='Venture 1', symbol='v1',
        )
        self.venture_role = VentureRole.objects.create(
            id=11111,
            name='abcd',
            venture=self.venture1
        )
        self.device = Device.create(
            sn='12345',
            model_name='Juniper stacked switch',
            model_type=DeviceType.switch_stack,
            service=ServiceCatalogFactory(
                name='service-1', uid='sc-1'
            ),
            device_environment=DeviceEnvironmentFactory(
                id=9876, name='prod'
            ),
            venture=self.venture1,
            venture_role=self.venture_role,
        )
        self.device.name = 'ss-1.mydc.net'
        self.device.save()
        self.child1_device.name = 'sw1-0.mydc.net'
        self.child1_device.logical_parent = self.device
        self.child1_device.save()
        self.child2_device.name = 'sw1-1.mydc.net'
        self.child2_device.logical_parent = self.device
        self.child2_device.save()

        property_symbol = 'test_symbol'
        property_value = 'test_value'
        self.device.venture_role.roleproperty_set.create(symbol=property_symbol)
        self.device.set_property(property_symbol, property_value, None)

        self.maxDiff = None

    def test_sync_stacked_switch(self):
        result = sync_stacked_switch_to_ralph3(Device, self.device)
        child_devices = result.pop('child_devices')
        self.assertEqual(result, {
            'hostname': 'ss-1.mydc.net',
            'custom_fields': {'test_symbol': 'test_value'},
            'environment': 9876,
            'id': self.device.id,
            'service': 'sc-1',
            'type': 'Juniper stacked switch',
            'venture_role': 11111,
        })
        self.assertItemsEqual(child_devices, [
            {'asset_id': self.child1.id, 'is_master': True},
            {'asset_id': self.child2.id, 'is_master': False}
        ])
