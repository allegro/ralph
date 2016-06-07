from django.test import TestCase

from ralph.ralph2_sync.publishers import sync_dc_asset_to_ralph2
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.models.choices import DataCenterAssetStatus
from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.data_importer.models import ImportedObjects


class DCAssetPublisherTestCase(TestCase):
    def setUp(self):
        self.dc_asset = DataCenterAssetFactory(
            orientation=1,
            position=10,
            sn='sn12345',
            barcode='bc12345',
            slot_no='1a',
            price=1000,
            niw='11111',
            task_url='http://ralph.com/1234',
            remarks='some notes',
            order_no='ORDER-1234',
            invoice_date='2016-06-01',
            invoice_no='INVOICE-1234',
            provider='Dell',
            source=1,
            status=DataCenterAssetStatus.new.id,
            depreciation_rate=25,
            force_depreciation=False,
            depreciation_end_date='2016-07-01',
            management_ip='10.20.30.40',
            management_hostname='mgmt11.my.dc',
            service_env=ServiceEnvironmentFactory(),
            rack=RackFactory(),
        )
        self.ralph2_dc_id = "11"
        ImportedObjects.create(
            self.dc_asset.rack.server_room.data_center, self.ralph2_dc_id
        )
        self.ralph2_server_room_id = "22"
        ImportedObjects.create(
            self.dc_asset.rack.server_room, self.ralph2_server_room_id
        )
        self.ralph2_rack_id = "33"
        ImportedObjects.create(self.dc_asset.rack, self.ralph2_rack_id)

        self.ralph2_service_id = "44"
        ImportedObjects.create(
            self.dc_asset.service_env.service, self.ralph2_service_id
        )
        self.ralph2_environment_id = "55"
        ImportedObjects.create(
            self.dc_asset.service_env.environment, self.ralph2_environment_id
        )

        self.ralph2_model_id = "66"
        ImportedObjects.create(
            self.dc_asset.model, self.ralph2_model_id
        )
        self.ralph2_category_id = "77"
        ImportedObjects.create(
            self.dc_asset.model.category, self.ralph2_category_id
        )

        self.ralph2_dc_asset_id = "88"
        ImportedObjects.create(self.dc_asset, self.ralph2_dc_asset_id)

        self.maxDiff = None

    def test_publishing_dc_asset(self):
        result = sync_dc_asset_to_ralph2(DataCenterAsset, self.dc_asset)
        self.assertEqual(result, {
            "model_info": {
                "cores_count": 0,
                "category": "2-2-2-data-center-device-switch-ethernet-rack",
                "id": 171,
                "power_consumption": 150,
                "manufacturer": "7",
                "height_of_device": 1.0
            },
            "barcode": "bc12345",
            "data_center": self.ralph2_dc_id,
            "depreciation_end_date": "2016-07-01",
            "depreciation_rate": "25.00",
            "environment": self.ralph2_environment_id,
            "force_depreciation": False,
            "id": str(self.dc_asset.id),
            "invoice_date": "2016-06-01",
            "invoice_no": "INVOICE-1234",
            "management_hostname": "mgmt11.my.dc",
            "management_ip": "10.20.30.40",
            "model": self.ralph2_model_id,
            "niw": "11111",
            "order_no": "ORDER-1234",
            "orientation": "1",
            "position": "10",
            "price": "1000",
            "property_of": None,  # TODO
            "provider": "Dell",
            "rack": self.ralph2_rack_id,
            "ralph2_id": self.ralph2_dc_asset_id,
            "remarks": "some notes",
            "server_room": self.ralph2_server_room_id,
            "service": self.ralph2_service_id,
            "slot_no": "1a",
            "sn": "sn12345",
            "source": 1,
            "status": str(DataCenterAssetStatus.new.id),
            "task_url": "http://ralph.com/1234",
        })
