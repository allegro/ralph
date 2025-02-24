import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from ralph.assets.models.choices import ObjectModelType
from ralph.assets.tests.factories import (
    DataCenterAssetModelFactory,
    EnvironmentFactory,
    ServiceEnvironment,
    ServiceFactory
)
from ralph.data_center.models.choices import Orientation
from ralph.data_center.tests.factories import (
    AccessoryFactory,
    DataCenterAssetFactory,
    RackAccessoryFactory,
    RackFactory,
    ServerRoomFactory
)
from ralph.dc_view.serializers.models_serializer import (
    TYPE_ACCESSORY,
    TYPE_ASSET
)


class TestRestAssetInfoPerRack(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser("test", "test@test.test", "test")

        self.client = APIClient()
        self.client.login(username="test", password="test")

        environment = EnvironmentFactory()
        service = ServiceFactory(name="Service1")
        service_env = ServiceEnvironment.objects.create(
            service=service, environment=environment
        )
        asset_model = DataCenterAssetModelFactory(type=ObjectModelType.data_center)
        self.server_room = ServerRoomFactory()

        self.accesory_1 = AccessoryFactory()

        self.rack_1 = RackFactory(server_room=self.server_room, max_u_height=3)

        self.asset_1 = DataCenterAssetFactory(
            service_env=service_env,
            position=1,
            slot_no="",
            force_depreciation=False,
            model=asset_model,
            rack=self.rack_1,
        )
        self.asset_1.management_ip = "10.15.25.45"

        self.pdu_1 = DataCenterAssetFactory(
            service_env=service_env,
            rack=self.rack_1,
            orientation=Orientation.left,
            force_depreciation=False,
            model=asset_model,
            position=0,
        )
        self.rack1_accessory = RackAccessoryFactory(
            rack=self.rack_1,
            orientation=Orientation.front,
            accessory=self.accesory_1,
            position=1,
        )

    def tearDown(self):
        self.client.logout()

    def test_get(self):
        returned_json = json.loads(
            self.client.get("/api/rack/{0}/".format(self.rack_1.id)).content.decode()
        )
        self.maxDiff = None
        expected_json = {
            "info": {
                "id": self.rack_1.id,
                "name": self.rack_1.name,
                "server_room": self.rack_1.server_room.id,
                "max_u_height": self.rack_1.max_u_height,
                "visualization_col": self.rack_1.visualization_col,
                "visualization_row": self.rack_1.visualization_row,
                "free_u": self.rack_1.get_free_u(),
                "description": "{}".format(self.rack_1.description),
                "orientation": "{}".format(self.rack_1.get_orientation_desc()),
                "rack_admin_url": self.rack_1.get_absolute_url(),
                "reverse_ordering": self.rack_1.reverse_ordering,
            },
            "devices": [
                {
                    "_type": TYPE_ASSET,
                    "id": self.asset_1.id,
                    "hostname": self.asset_1.hostname,
                    "category": self.asset_1.model.category.name,
                    "barcode": self.asset_1.barcode,
                    "sn": self.asset_1.sn,
                    "height": float(self.asset_1.model.height_of_device),
                    "position": self.asset_1.position,
                    "model": self.asset_1.model.name,
                    "children": [],
                    "front_layout": "",
                    "back_layout": "",
                    "management_ip": self.asset_1.management_ip,
                    "orientation": "front",
                    "remarks": "",
                    "service": "Service1",
                    "url": self.asset_1.get_absolute_url(),
                },
                {
                    "_type": TYPE_ACCESSORY,
                    "orientation": "front",
                    "position": self.rack1_accessory.position,
                    "remarks": self.rack1_accessory.remarks,
                    "type": self.rack1_accessory.accessory.name,
                    "url": self.rack1_accessory.get_absolute_url(),
                },
            ],
            "pdus": [
                {
                    "model": self.pdu_1.model.name,
                    "orientation": "left",
                    "sn": self.pdu_1.sn,
                    "url": self.pdu_1.get_absolute_url(),
                },
            ],
        }
        self.assertEqual(returned_json, expected_json)
