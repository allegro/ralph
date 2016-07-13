from django.test import override_settings, TestCase

from ralph.assets.models import AssetModel
from ralph.assets.tests.factories import (
    DataCenterAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.models.choices import DataCenterAssetStatus
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.data_importer.models import ImportedObjects
from ralph.ralph2_sync.publishers import (
    sync_dc_asset_to_ralph2,
    sync_model_to_ralph2,
    sync_virtual_server_to_ralph2
)
from ralph.virtual.models import VirtualServer
from ralph.virtual.tests.factories import VirtualServerFactory


@override_settings(RALPH2_HERMES_SYNC_ENABLED=True)
class DCAssetPublisherTestCase(TestCase):
    def setUp(self):
        self.dc_asset = DataCenterAssetFactory(
            barcode='bc12345',
            depreciation_end_date='2016-07-01',
            depreciation_rate=25,
            force_depreciation=False,
            hostname='my-host.mydc.net',
            invoice_date='2016-06-01',
            invoice_no='INVOICE-1234',
            niw='11111',
            order_no='ORDER-1234',
            orientation=1,
            position=10,
            price=1000,
            provider='Dell',
            rack=RackFactory(),
            remarks='some notes',
            service_env=ServiceEnvironmentFactory(service__uid='sc-1234'),
            slot_no='1a',
            sn='sn12345',
            source=1,
            status=DataCenterAssetStatus.new.id,
            task_url='http://ralph.com/1234',
        )
        self.dc_asset.management_ip = '10.20.30.40'
        self.dc_asset.management_hostname = 'mgmt11.my.dc'

        self.ralph2_dc_id = '11'
        ImportedObjects.create(
            self.dc_asset.rack.server_room.data_center, self.ralph2_dc_id
        )
        self.ralph2_server_room_id = '22'
        ImportedObjects.create(
            self.dc_asset.rack.server_room, self.ralph2_server_room_id
        )
        self.ralph2_rack_id = '33'
        ImportedObjects.create(self.dc_asset.rack, self.ralph2_rack_id)

        self.ralph2_environment_id = '55'
        ImportedObjects.create(
            self.dc_asset.service_env.environment, self.ralph2_environment_id
        )

        self.ralph2_model_id = '66'
        ImportedObjects.create(self.dc_asset.model, self.ralph2_model_id)
        self.ralph2_property_of_id = '77'
        ImportedObjects.create(
            self.dc_asset.property_of, self.ralph2_property_of_id
        )

        self.ralph2_venture_id = '99'
        ImportedObjects.create(
            self.dc_asset.configuration_path.module, self.ralph2_venture_id
        )

        self.ralph2_venture_role_id = '990'
        ImportedObjects.create(
            self.dc_asset.configuration_path, self.ralph2_venture_role_id
        )

        self.ralph2_dc_asset_id = '88'
        ImportedObjects.create(self.dc_asset, self.ralph2_dc_asset_id)

        self.maxDiff = None

    @override_settings(RALPH2_HERMES_SYNC_FUNCTIONS=['sync_dc_asset_to_ralph2'])
    def test_publishing_dc_asset(self):
        result = sync_dc_asset_to_ralph2(DataCenterAsset, self.dc_asset)
        self.assertEqual(result, {
            'barcode': 'bc12345',
            'data_center': '11',
            'depreciation_end_date': '2016-07-01',
            'depreciation_rate': '25',
            'environment': '55',
            'force_depreciation': False,
            'hostname': 'my-host.mydc.net',
            'id': str(self.dc_asset.id),
            'invoice_date': '2016-06-01',
            'invoice_no': 'INVOICE-1234',
            'management_hostname': 'mgmt11.my.dc',
            'management_ip': '10.20.30.40',
            'model': '66',
            'niw': '11111',
            'order_no': 'ORDER-1234',
            'orientation': '1',
            'position': '10',
            'price': '1000',
            'property_of': '77',
            'provider': 'Dell',
            'rack': '33',
            'ralph2_id': '88',
            'remarks': 'some notes',
            'server_room': '22',
            'service': 'sc-1234',
            'slot_no': '1a',
            'sn': 'sn12345',
            'source': '1',
            'status': str(DataCenterAssetStatus.new.id),
            'task_url': 'http://ralph.com/1234',
            'custom_fields': {},
            'venture': self.ralph2_venture_id,
            'venture_role': self.ralph2_venture_role_id,
        })


@override_settings(RALPH2_HERMES_SYNC_ENABLED=True)
class AssetModelPublisherTestCase(TestCase):
    def setUp(self):
        self.model = DataCenterAssetModelFactory(
            name='test model',
            cores_count=10,
            power_consumption=11,
            height_of_device=12,
        )
        self.ralph2_manufacturer_id = '11'
        ImportedObjects.create(
            self.model.manufacturer, self.ralph2_manufacturer_id
        )
        self.ralph2_category_id = '22'
        ImportedObjects.create(
            self.model.category, self.ralph2_category_id
        )
        self.ralph2_model_id = '33'
        ImportedObjects.create(
            self.model, self.ralph2_model_id
        )

    @override_settings(RALPH2_HERMES_SYNC_FUNCTIONS=['sync_model_to_ralph2'])
    def test_publishing_model(self):
        result = sync_model_to_ralph2(AssetModel, self.model)
        self.assertEqual(result, {
            'id': self.model.id,
            'ralph2_id': '33',
            'name': 'test model',
            'category': '22',
            'cores_count': 10,
            'power_consumption': 11,
            'height_of_device': 12,
            'manufacturer': '11',
        })


@override_settings(RALPH2_HERMES_SYNC_ENABLED=True)
class VirtualServerPublisherTestCase(TestCase):
    def setUp(self):
        hypervisor = DataCenterAssetFactory()
        self.old_vs_id = 123
        self.old_hypervisor_id = 987
        self.old_env_id = 786
        self.vs = VirtualServerFactory(parent=hypervisor)
        ImportedObjects.create(
            self.vs, self.old_vs_id
        )
        ImportedObjects.create(
            hypervisor, self.old_hypervisor_id
        )
        ImportedObjects.create(
            self.vs.service_env.environment, self.old_env_id
        )

    @override_settings(RALPH2_HERMES_SYNC_FUNCTIONS=[
        'sync_virtual_server_to_ralph2'
    ])
    def test_publishing(self):
        result = sync_virtual_server_to_ralph2(VirtualServer, self.vs)
        self.assertEqual(result, {
            'id': self.vs.id,
            'ralph2_id': str(self.old_vs_id),
            'ralph2_parent_id': str(self.old_hypervisor_id),
            'hostname': self.vs.hostname,
            'sn': self.vs.sn,
            'type': self.vs.type.name,
            'service_uid': self.vs.service_env.service.uid,
            'environment_id': str(self.old_env_id),
            'venture_id': None,
            'venture_role_id': None,
            'custom_fields': {},
        })
