from django.test import TestCase
from django.test.utils import override_settings

from ralph.cmdb.tests.utils import (
    DeviceEnvironmentFactory,
    ServiceCatalogFactory
)
from ralph.discovery.models import DeviceType, Device
from ralph.export_to_ng.publishers import sync_device_to_ralph3
from ralph_assets.tests.utils.assets import DCAssetFactory


@override_settings(
    RALPH3_HERMES_SYNC_ENABLED=True,
    RALPH3_HERMES_SYNC_FUNCTIONS=['sync_device_to_ralph3'])
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
        })
