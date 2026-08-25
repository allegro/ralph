import json

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from ralph.assets.models.choices import ObjectModelType
from ralph.assets.tests.factories import (
    DataCenterAssetModelFactory,
    EnvironmentFactory,
    ServiceFactory,
    ServiceEnvironmentFactory,
)
from ralph.data_center.models.choices import Orientation
from ralph.data_center.tests.factories import (
    AccessoryFactory,
    DataCenterAssetFactory,
    RackAccessoryFactory,
    RackFactory,
    ServerRoomFactory,
)
from ralph.dc_view.serializers.models_serializer import (
    TYPE_ACCESSORY,
    TYPE_ASSET,
    DataCenterAssetSerializer,
)
from ralph.switchports.tests.factories import ConnectionFactory, PortFactory


class TestRestAssetInfoPerRack(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser("test", "test@test.test", "test")

        self.client = APIClient()
        self.client.login(username="test", password="test")

        environment = EnvironmentFactory()
        service = ServiceFactory(name="Service1")
        service_env = ServiceEnvironmentFactory(service=service, environment=environment)
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
                "is_active": self.rack_1.active,
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
                    "metadata": None,
                    "service": "Service1",
                    "url": self.asset_1.get_absolute_url(),
                    "ports_url": reverse(
                        "admin:data_center_datacenterasset_ports", args=(self.asset_1.id,)
                    ),
                    "ports": None,
                    "free_ports": None,
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

    def test_ports_are_not_queried_when_disabled_for_category(self):
        with CaptureQueriesContext(connection) as queries:
            data = DataCenterAssetSerializer(self.asset_1).data

        port_queries = [query for query in queries if "switchports_port" in query["sql"]]
        self.assertEqual(data["ports"], None)
        self.assertEqual(data["free_ports"], None)
        self.assertEqual(port_queries, [])

    def test_ports_are_returned_when_enabled_for_category(self):
        category = self.asset_1.model.category
        category.show_ports_in_visualization = True
        category.save(update_fields=["show_ports_in_visualization"])
        ports = [
            PortFactory(label="0/0/{}".format(index), data_center_asset=self.asset_1)
            for index in range(3)
        ]
        ConnectionFactory(post_members=[ports[0]])

        with CaptureQueriesContext(connection) as queries:
            data = DataCenterAssetSerializer(self.asset_1).data

        port_queries = [query for query in queries if "switchports_port" in query["sql"]]
        self.assertEqual(data["ports"], 3)
        self.assertEqual(data["free_ports"], 2)
        self.assertEqual(len(port_queries), 1)

    def test_port_counts_are_not_queried_per_asset_in_rack_view(self):
        """
        Verifies that retrieving port counts for multiple assets in a rack does
        not result in one DB query per asset (N+1). The annotation should batch
        all counts into a single query.
        """
        category = self.asset_1.model.category
        category.show_ports_in_visualization = True
        category.save(update_fields=["show_ports_in_visualization"])

        asset_2 = DataCenterAssetFactory(
            model=self.asset_1.model,
            rack=self.rack_1,
            position=2,
            slot_no="",
        )

        ports_1 = [
            PortFactory(label="0/0/{}".format(i), data_center_asset=self.asset_1) for i in range(2)
        ]
        ConnectionFactory(post_members=[ports_1[0]])

        PortFactory(label="0/1/0", data_center_asset=asset_2)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/rack/{}/".format(self.rack_1.id))

        port_queries = [q for q in queries if "switchports_port" in q["sql"]]
        self.assertEqual(len(port_queries), 1)

        devices = {d["id"]: d for d in response.data["devices"] if d.get("_type") == TYPE_ASSET}
        self.assertEqual(devices[self.asset_1.id]["ports"], 2)
        self.assertEqual(devices[self.asset_1.id]["free_ports"], 1)
        self.assertEqual(devices[asset_2.id]["ports"], 1)
        self.assertEqual(devices[asset_2.id]["free_ports"], 1)
