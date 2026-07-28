from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports import grid
from ralph.switchports.models import (
    Connection,
    ConnectionMember,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
)
from ralph.switchports.rackconfig.overrides import build_override_map
from ralph.switchports.rackconfig.port_labels import to_display


class GridTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-Grid")
        self.switch_eth1 = DataCenterAssetFactory(hostname="rack101.sw.eth1.local")
        self.switch_eth2 = DataCenterAssetFactory(hostname="rack101.sw.eth2.local")
        self.switch_mgmt = DataCenterAssetFactory(hostname="rack101.sw.mgmt.local")

        self.server1 = DataCenterAssetFactory(
            hostname="srv1.example.com", rack=self.rack, position=1
        )
        self.server2 = DataCenterAssetFactory(
            hostname="srv2.example.com", rack=self.rack, position=2
        )

        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        self.sc_eth1 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_eth1,
            label="eth1",
        )
        self.sc_eth2 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_eth2,
            label="eth2",
        )
        self.sc_mgmt = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_mgmt,
            label="mgmt",
        )

    def _assets_and_configs(self):
        assets = list(grid.get_rack_assets(self.rack))
        switch_configs = list(grid.get_switch_configs(self.rack_config))
        return assets, switch_configs

    def test_get_rack_assets_returns_assets_in_rack(self):
        assets = list(grid.get_rack_assets(self.rack))
        hostnames = [a.hostname for a in assets]
        self.assertIn("srv1.example.com", hostnames)
        self.assertIn("srv2.example.com", hostnames)

    def test_get_switch_configs_returns_all_configs(self):
        configs = list(grid.get_switch_configs(self.rack_config))
        labels = [c.label for c in configs]
        self.assertEqual(sorted(labels), ["eth1", "eth2", "mgmt"])

    def test_build_connection_map_empty_when_no_connections(self):
        assets, switch_configs = self._assets_and_configs()
        connection_map = grid.build_connection_map(assets, switch_configs)
        self.assertEqual(connection_map, {})

    def test_build_connection_map_finds_existing_connections(self):
        # Connect server1:eth1 <-> switch_eth1:0/0/20
        asset_port = Port.objects.create(label="eth1", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="0/0/20", data_center_asset=self.switch_eth1
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        assets, switch_configs = self._assets_and_configs()
        connection_map = grid.build_connection_map(assets, switch_configs)

        key = (self.server1.id, self.sc_eth1.id)
        self.assertIn(key, connection_map)
        self.assertEqual(connection_map[key]["switch_port_label"], "0/0/20")
        self.assertEqual(connection_map[key]["asset_port_label"], "eth1")

    def test_grid_rows_built_correctly(self):
        assets, switch_configs = self._assets_and_configs()
        override_map = build_override_map(switch_configs)
        connection_map = grid.build_connection_map(assets, switch_configs)
        validation_map, switch_status = grid.build_validation_map(self.rack_config)

        rows = grid.build_grid_rows(
            assets,
            switch_configs,
            override_map,
            connection_map,
            validation_map,
            switch_status,
            has_validation=False,
        )

        # 3 switch configs -> 3 cells per row
        for row in rows:
            self.assertEqual(len(row["cells"]), 3)
        # 2 assets in the rack -> 2 rows
        self.assertEqual(len(rows), 2)

    def test_conflict_cell_renders_typed_value_and_force_field(self):
        assets, switch_configs = self._assets_and_configs()
        override_map = build_override_map(switch_configs)
        connection_map = grid.build_connection_map(assets, switch_configs)
        validation_map, switch_status = grid.build_validation_map(self.rack_config)
        conflicts = {
            (self.server1.id, self.sc_eth1.id): {
                "typed_value": "30",
                "typed_override": "",
                "owner_hostname": "srv2.example.com",
                "owner_barcode": "2135554",
                "owner_sn": "1234566213",
                "switch_hostname": self.switch_eth1.hostname,
                "switch_port_label": "0/0/30",
            }
        }

        rows = grid.build_grid_rows(
            assets,
            switch_configs,
            override_map,
            connection_map,
            validation_map,
            switch_status,
            has_validation=False,
            conflicts=conflicts,
        )

        conflict_cells = [
            cell for row in rows for cell in row["cells"] if cell.get("is_conflict")
        ]
        self.assertEqual(len(conflict_cells), 1)
        cell = conflict_cells[0]
        self.assertEqual(cell["value"], "30")
        self.assertEqual(cell["conflict_owner"], "2135554")
        self.assertEqual(
            cell["force_field_name"],
            f"force_{self.server1.id}_{self.sc_eth1.id}",
        )
        self.assertIsNone(cell["validation"])

    def test_grid_shows_existing_port_number(self):
        # Connect server1:eth1 <-> switch_eth1:0/0/42
        asset_port = Port.objects.create(label="eth1", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="0/0/42", data_center_asset=self.switch_eth1
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        assets, switch_configs = self._assets_and_configs()
        connection_map = grid.build_connection_map(assets, switch_configs)

        conn_info = connection_map.get((self.server1.id, self.sc_eth1.id))
        self.assertIsNotNone(conn_info)
        # "0/0/42" -> display as "42"
        self.assertEqual(to_display(conn_info["switch_port_label"]), "42")

    def test_nonstandard_port_label_passes_through(self):
        """Port labels like '1/0/5' are not stripped."""
        asset_port = Port.objects.create(label="eth2", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="1/0/5", data_center_asset=self.switch_eth2
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        assets, switch_configs = self._assets_and_configs()
        connection_map = grid.build_connection_map(assets, switch_configs)

        conn_info = connection_map.get((self.server1.id, self.sc_eth2.id))
        self.assertIsNotNone(conn_info)
        self.assertEqual(conn_info["switch_port_label"], "1/0/5")
