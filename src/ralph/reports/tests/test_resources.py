from random import randint

from ralph.assets.tests.factories import (
    DataCenterAssetModelFactory,
    EthernetFactory
)
from ralph.data_center.models import Orientation, RackOrientation
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.networks.tests.factories import IPAddressFactory
from ralph.reports.resources import DataCenterAssetTextResource
from ralph.tests import RalphTestCase


class TestEmailReports(RalphTestCase):
    def setUp(self):
        self.rack = RackFactory()
        self.asset = DataCenterAssetFactory(rack=self.rack, position=randint(0, 100))
        self.ethernets = EthernetFactory.create_batch(2, base_object=self.asset)
        self.ip = IPAddressFactory(
            base_object=self.asset, is_management=False, ethernet=self.ethernets[0]
        )
        self.management = IPAddressFactory(
            base_object=self.asset, is_management=True, ethernet=self.ethernets[1]
        )

    def test_dataset_contains_asset_data(self):
        dataset = DataCenterAssetTextResource().export()
        lines = dataset.csv.split("\r\n")

        expected_headers = (
            "dc,server_room,rack,rack_orientation,"
            "orientation,position,model,hostname,"
            "management_ip,ip,barcode,sn,service_uid,service,"
            "environment,configuration_path"
        )
        expected_line_data = [
            self.rack.server_room.data_center.name,
            self.rack.server_room.name,
            self.rack.name,
            RackOrientation.from_id(self.rack.orientation).name,
            Orientation.from_id(self.asset.orientation).name,
            str(self.asset.position),
            self.asset.model.name,
            self.asset.hostname,
            self.management.address,
            self.ip.address,
            self.asset.barcode,
            self.asset.sn,
            self.asset.service_env.service.uid,
            self.asset.service_env.service.name,
            self.asset.service_env.environment.name,
            self.asset.configuration_path.path,
        ]
        expected_line = ",".join(expected_line_data)
        self.assertEqual(expected_headers, lines[0])
        self.assertEqual(expected_line, lines[1])

    def test_queries_number(self):
        for _ in range(0, 10):
            rack = RackFactory()
            for position in range(1, 6):
                model = DataCenterAssetModelFactory(has_parent=True)
                asset = DataCenterAssetFactory(
                    rack=rack, position=position, model=model
                )
                ethernets = EthernetFactory.create_batch(2, base_object=asset)
                IPAddressFactory(
                    base_object=asset, is_management=False, ethernet=ethernets[0]
                )
                IPAddressFactory(
                    base_object=asset, is_management=True, ethernet=ethernets[1]
                )
        with self.assertNumQueries(103):
            DataCenterAssetTextResource().export()
