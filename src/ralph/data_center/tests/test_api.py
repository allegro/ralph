# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    DataCenterAssetModelFactory,
    EthernetFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.models import (
    BaseObjectCluster,
    Cluster,
    DataCenterAsset,
    Orientation,
    Rack,
    RackAccessory,
    RackOrientation
)
from ralph.data_center.tests.factories import (
    AccessoryFactory,
    ClusterFactory,
    ClusterTypeFactory,
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
    RackAccessoryFactory,
    RackFactory,
    ServerRoomFactory
)
from ralph.networks.tests.factories import IPAddressFactory
from ralph.virtual.tests.factories import CloudHostFactory, VirtualServerFactory


class DataCenterAssetAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.service_env = ServiceEnvironmentFactory()
        self.model = DataCenterAssetModelFactory()
        self.assetHolder = AssetHolderFactory()
        self.rack = RackFactory()
        self.dc_asset = DataCenterAssetFullFactory(
            rack=self.rack,
            position=10,
            model=self.model,
            service_env__environment__name="some_env",
        )
        self.dc_asset.service_env.service.business_owners.set([self.user1])
        self.dc_asset.service_env.service.technical_owners.set([self.user2])
        self.ip = IPAddressFactory(ethernet=EthernetFactory(base_object=self.dc_asset))
        self.dc_asset.tags.add("db", "test")
        self.dc_asset_2 = DataCenterAssetFullFactory(rack=self.rack)

    def test_get_data_center_assets_list(self):
        DataCenterAssetFullFactory.create_batch(100)
        url = reverse("datacenterasset-list") + "?limit=100"
        with self.assertNumQueries(21):
            response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], DataCenterAsset.objects.count())

    def test_get_data_center_asset_details(self):
        url = reverse("datacenterasset-detail", args=(self.dc_asset.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hostname"], self.dc_asset.hostname)
        self.assertEqual(response.data["rack"]["id"], self.dc_asset.rack.id)
        self.assertEqual(response.data["model"]["id"], self.dc_asset.model.id)
        self.assertEqual(len(response.data["ethernet"]), 4)
        self.assertIn(
            self.ip.address,
            [
                eth["ipaddress"]["address"]
                for eth in response.data["ethernet"]
                if eth["ipaddress"]
            ],
        )
        self.assertEqual(len(response.data["memory"]), 2)
        self.assertEqual(response.data["memory"][0]["speed"], 1600)
        self.assertEqual(response.data["memory"][0]["size"], 8192)
        self.assertEqual(response.data["business_owners"][0]["username"], "user1")
        self.assertEqual(response.data["technical_owners"][0]["username"], "user2")

    def test_get_data_center_asset_details_related_hosts(self):
        dc_asset_3 = DataCenterAssetFullFactory()
        cloud_host = CloudHostFactory(hypervisor=dc_asset_3)
        virtual_server = VirtualServerFactory(parent=dc_asset_3)
        virtual_server_2 = VirtualServerFactory(
            parent=dc_asset_3, hostname="random_test_hostname"
        )
        dc_asset_4 = DataCenterAssetFullFactory(parent=dc_asset_3)
        url = reverse("datacenterasset-detail", args=(dc_asset_3.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(len(response.data["related_hosts"]["cloud_hosts"]), 1)
        self.assertEqual(len(response.data["related_hosts"]["virtual_servers"]), 2)
        self.assertIn(
            response.data["related_hosts"]["virtual_servers"][0]["hostname"],
            (virtual_server.hostname, virtual_server_2.hostname),
        )
        self.assertIn(
            response.data["related_hosts"]["virtual_servers"][1]["hostname"],
            (virtual_server.hostname, virtual_server_2.hostname),
        )
        self.assertEqual(
            response.data["related_hosts"]["cloud_hosts"][0]["hostname"],
            cloud_host.hostname,
        )
        self.assertEqual(len(response.data["related_hosts"]["physical_servers"]), 1)
        self.assertEqual(
            response.data["related_hosts"]["physical_servers"][0]["hostname"],
            dc_asset_4.hostname,
        )

    def test_get_data_center_asset_list_related_hosts(self):
        dc_asset_5 = DataCenterAssetFullFactory()
        cloud_host = CloudHostFactory(hypervisor=dc_asset_5)
        virtual_server = VirtualServerFactory(parent=dc_asset_5)
        virtual_server_2 = VirtualServerFactory(
            parent=dc_asset_5, hostname="random_test_hostname"
        )
        dc_asset_6 = DataCenterAssetFullFactory(parent=dc_asset_5)
        url = f"{reverse('datacenterasset-list')}?hostname={dc_asset_5.hostname}"
        response = self.client.get(url, format="json")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            len(response.data["results"][0]["related_hosts"]["cloud_hosts"]), 1
        )
        self.assertEqual(
            len(response.data["results"][0]["related_hosts"]["virtual_servers"]), 2
        )
        self.assertIn(
            response.data["results"][0]["related_hosts"]["virtual_servers"][0][
                "hostname"
            ],
            (virtual_server.hostname, virtual_server_2.hostname),
        )
        self.assertIn(
            response.data["results"][0]["related_hosts"]["virtual_servers"][1][
                "hostname"
            ],
            (virtual_server.hostname, virtual_server_2.hostname),
        )
        self.assertEqual(
            response.data["results"][0]["related_hosts"]["cloud_hosts"][0]["hostname"],
            cloud_host.hostname,
        )
        self.assertEqual(
            len(response.data["results"][0]["related_hosts"]["physical_servers"]), 1
        )
        self.assertEqual(
            response.data["results"][0]["related_hosts"]["physical_servers"][0][
                "hostname"
            ],
            dc_asset_6.hostname,
        )

    def test_create_data_center_asset(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "barcode": "12345",
            "model": self.model.id,
            "rack": self.rack.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
            "property_of": self.assetHolder.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dc_asset = DataCenterAsset.objects.get(pk=response.data["id"])
        self.assertEqual(dc_asset.hostname, "12345")
        self.assertEqual(dc_asset.service_env, self.service_env)
        self.assertEqual(dc_asset.rack, self.rack)

    def test_create_data_center_asset_without_rack(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "barcode": "12345",
            "model": self.model.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "rack": ["This field is required."],
            },
        )

    def test_create_data_center_asset_with_rack_null(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "barcode": "12345",
            "rack": None,
            "model": self.model.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "rack": ["This field may not be null."],
            },
        )

    def test_create_data_center_with_tags(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "barcode": "12345",
            "model": self.model.id,
            "rack": self.rack.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
            "tags": ["prod", "db"],
            "property_of": self.assetHolder.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dc_asset = DataCenterAsset.objects.get(pk=response.data["id"])
        self.assertEqual(dc_asset.hostname, "12345")
        self.assertEqual(dc_asset.service_env, self.service_env)
        self.assertEqual(dc_asset.rack, self.rack)
        self.assertEqual(dc_asset.tags.count(), 2)

    def test_create_data_center_without_barcode_and_sn(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "model": self.model.id,
            "rack": self.rack.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
            "tags": ["prod", "db"],
            "property_of": self.assetHolder.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "sn": ["SN or BARCODE field is required"],
                "barcode": ["SN or BARCODE field is required"],
            },
        )

    def test_create_data_center_without_property_of(self):
        url = reverse("datacenterasset-list")
        data = {
            "hostname": "12345",
            "model": self.model.id,
            "rack": self.rack.id,
            "position": 12,
            "service_env": self.service_env.id,
            "force_depreciation": False,
            "tags": ["prod", "db"],
            "sn": "sn",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "__all__": ["Property of field is required"],
            },
        )

    def test_patch_data_center_asset(self):
        url = reverse("datacenterasset-detail", args=(self.dc_asset.id,))
        data = {"hostname": "54321", "force_depreciation": True, "tags": ["net"]}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.hostname, "54321")
        self.assertTrue(self.dc_asset.force_depreciation)
        self.assertEqual(self.dc_asset.tags.count(), 1)

    def test_update_vendor_contract_number_and_leasing_rate(self):
        url = reverse("datacenterasset-detail", args=(self.dc_asset.id,))
        hostname = self.dc_asset.hostname
        data = {"vendor_contract_number": "abc-123", "leasing_rate": 123.45}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dc_asset.refresh_from_db()
        self.assertEqual(self.dc_asset.hostname, hostname)
        self.assertEqual(self.dc_asset.vendor_contract_number, "abc-123")
        self.assertEqual(self.dc_asset.leasing_rate, 123.45)

    def test_filter_by_configuration_path(self):
        url = reverse("datacenterasset-list") + "?configuration_path={}".format(
            self.dc_asset.configuration_path.path,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_hostname(self):
        url = reverse("datacenterasset-list") + "?hostname={}".format(
            self.dc_asset.hostname,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_ip_address(self):
        url = reverse("datacenterasset-list") + "?ip={}".format(
            self.ip.address,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_service_uid(self):
        url = reverse("datacenterasset-list") + "?service={}".format(
            self.dc_asset.service_env.service.uid,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_service_uid2(self):
        url = reverse("datacenterasset-list") + "?service_env__service__uid={}".format(
            self.dc_asset.service_env.service.uid,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_service_id(self):
        url = reverse("datacenterasset-list") + "?service_env__service__id={}".format(
            self.dc_asset.service_env.service.id,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_service_name(self):
        url = reverse("datacenterasset-list") + "?service={}".format(
            self.dc_asset.service_env.service.name,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_service_name2(self):
        url = reverse("datacenterasset-list") + "?service_env__service__name={}".format(
            self.dc_asset.service_env.service.name,
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_env_name(self):
        url = reverse("datacenterasset-list") + "?env=some_env"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class RackAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.server_room = ServerRoomFactory()
        self.accessory = AccessoryFactory()
        self.rack = RackFactory(server_room=self.server_room)
        self.rack_accessory = RackAccessoryFactory(
            accessory=self.accessory, rack=self.rack
        )

    def test_get_rack_list(self):
        url = reverse("rack-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], Rack.objects.count())

    def test_get_rack_details(self):
        url = reverse("rack-detail", args=(self.rack.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.rack.name)
        self.assertEqual(response.data["server_room"]["id"], self.server_room.id)
        self.assertEqual(
            response.data["server_room"]["data_center"]["id"],
            self.server_room.data_center.id,
        )
        accessory = response.data["accessories"][0]
        self.assertEqual(accessory["id"], self.rack_accessory.id)
        self.assertEqual(accessory["name"], self.rack_accessory.accessory.name)
        self.assertEqual(accessory["position"], self.rack_accessory.position)

    def test_create_rack(self):
        url = reverse("rack-list")
        data = {
            "name": "Rack 111",
            "server_room": self.server_room.id,
            "description": "My rack",
            "orientation": "bottom",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack = Rack.objects.get(pk=response.data["id"])
        self.assertEqual(rack.name, "Rack 111")
        self.assertEqual(rack.server_room, self.server_room)
        self.assertEqual(rack.description, "My rack")
        self.assertEqual(rack.orientation, RackOrientation.bottom)

    def test_create_rack_skip_accessories(self):
        # accessories should be created directly by RackAccessory - not assigned
        # by rack since it's m2m with through table
        url = reverse("rack-list")
        data = {
            "name": "Rack 111",
            "server_room": self.server_room.id,
            "accessories": [self.accessory.id],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack = Rack.objects.get(pk=response.data["id"])
        self.assertEqual(rack.accessories.count(), 0)

    def test_patch_rack(self):
        url = reverse("rack-detail", args=(self.rack.id,))
        data = {
            "name": "Rack 222",
            "description": "qwerty",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rack.refresh_from_db()
        self.assertEqual(self.rack.name, "Rack 222")
        self.assertEqual(self.rack.description, "qwerty")


class RackAccessoryAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.server_room = ServerRoomFactory()
        self.accessory = AccessoryFactory()
        self.rack = RackFactory(server_room=self.server_room)
        self.rack_accessory = RackAccessoryFactory(
            accessory=self.accessory, rack=self.rack
        )

    def test_get_rack_accessory_list(self):
        url = reverse("rackaccessory-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], RackAccessory.objects.count())

    def test_get_rack_accessory_details(self):
        url = reverse("rackaccessory-detail", args=(self.rack_accessory.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["rack"].endswith(
                reverse("rack-detail", args=(self.rack_accessory.rack.id,))
            )
        )
        self.assertTrue(
            response.data["accessory"].endswith(
                reverse("accessory-detail", args=(self.rack_accessory.accessory.id,))
            )
        )
        self.assertEqual(
            response.data["orientation"],
            Orientation.name_from_id(self.rack_accessory.orientation),
        )
        self.assertEqual(
            response.data["position"],
            self.rack_accessory.position,
        )

    def test_create_rack_accessory(self):
        url = reverse("rackaccessory-list")
        data = {
            "rack": self.rack.id,
            "accessory": self.accessory.id,
            "orientation": "front",
            "position": 11,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rack_accessory = RackAccessory.objects.get(pk=response.data["id"])
        self.assertEqual(rack_accessory.rack, self.rack)
        self.assertEqual(rack_accessory.accessory, self.accessory)
        self.assertEqual(rack_accessory.orientation, Orientation.front.id)
        self.assertEqual(rack_accessory.position, 11)

    def test_patch_rack_accessory(self):
        url = reverse("rackaccessory-detail", args=(self.rack_accessory.id,))
        data = {
            "remarks": "qwerty",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rack_accessory.refresh_from_db()
        self.assertEqual(self.rack_accessory.remarks, "qwerty")


class ClusterAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.cluster_type = ClusterTypeFactory()
        self.service_env = ServiceEnvironmentFactory()
        self.cluster_1 = ClusterFactory()
        self.boc_1 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=DataCenterAssetFactory()
        )
        self.master = DataCenterAssetFactory()
        self.boc_2 = BaseObjectCluster.objects.create(
            cluster=self.cluster_1, base_object=self.master, is_master=True
        )
        self.cluster_2 = ClusterFactory()
        self.cluster_1.service_env.service.business_owners.set([self.user1])
        self.cluster_1.service_env.service.technical_owners.set([self.user2])
        self.cluster_1.management_ip = "10.20.30.40"

    def test_create_cluster(self):
        url = reverse("cluster-list")
        data = {
            "type": self.cluster_type.id,
            "service_env": self.service_env.id,
            "name": "Test cluster",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cluster = Cluster.objects.get(pk=response.data["id"])
        self.assertEqual(cluster.name, "Test cluster")

    def test_create_cluster_with_hostname(self):
        url = reverse("cluster-list")
        data = {
            "type": self.cluster_type.id,
            "service_env": self.service_env.id,
            "hostname": "cluster1.mydc.net",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cluster = Cluster.objects.get(pk=response.data["id"])
        self.assertEqual(cluster.hostname, data["hostname"])

    def test_create_cluster_without_hostname_or_name(self):
        url = reverse("cluster-list")
        data = {
            "type": self.cluster_type.id,
            "service_env": self.service_env.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "name": ["At least one of name or hostname is required"],
                "hostname": ["At least one of name or hostname is required"],
            },
        )

    def test_list_cluster(self):
        ClusterFactory.create_batch(20)
        url = reverse("cluster-list") + "?limit=100"
        with self.assertNumQueries(13):
            response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 22)
        for item in response.data["results"]:
            if item["id"] == self.cluster_1.id:
                self.assertEqual(len(item["base_objects"]), 2)

    def test_get_cluster_details(self):
        url = reverse("cluster-detail", args=(self.cluster_1.id,))
        with self.assertNumQueries(12):
            response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.cluster_1.name)
        self.assertEqual(response.data["hostname"], self.cluster_1.hostname)
        self.assertEqual(response.data["business_owners"][0]["username"], "user1")
        self.assertEqual(response.data["technical_owners"][0]["username"], "user2")
        self.assertEqual(len(response.data["base_objects"]), 2)
        self.assertCountEqual(
            response.data["base_objects"],
            [
                {
                    "id": self.boc_1.id,
                    "url": self.get_full_url(
                        reverse("baseobjectcluster-detail", args=(self.boc_1.id,))
                    ),
                    "base_object": self.get_full_url(
                        reverse("baseobject-detail", args=(self.boc_1.base_object.id,))
                    ),
                    "is_master": self.boc_1.is_master,
                },
                {
                    "id": self.boc_2.id,
                    "url": self.get_full_url(
                        reverse("baseobjectcluster-detail", args=(self.boc_2.id,))
                    ),
                    "base_object": self.get_full_url(
                        reverse("baseobject-detail", args=(self.boc_2.base_object.id,))
                    ),
                    "is_master": self.boc_2.is_master,
                },
            ],
        )
        self.assertEqual(
            response.data["ethernet"][0]["ipaddress"]["address"], "10.20.30.40"
        )
        self.assertTrue(response.data["ethernet"][0]["ipaddress"]["is_management"])
        self.assertEqual(response.data["ipaddresses"], ["10.20.30.40"])
        self.assertEqual(
            response.data["masters"][0],
            self.get_full_url(reverse("baseobject-detail", args=(self.master.id,))),
        )
