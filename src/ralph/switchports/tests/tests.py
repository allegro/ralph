from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.dto import (
    InterfaceDTO,
    InterfaceMode,
    InterfaceStatus,
    SwitchDTO,
)
from ralph.switchports.models import (
    BackendValidationResult,
    Connection,
    ConnectionMember,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
    ValidationStatus,
)
from ralph.switchports.validation import refresh_validation_for_rack
from ralph.switchports.views import RackSwitchportGridView, _port_label_for_switch


class GenerateSwitchportGraphCommandTestCase(TestCase):
    def setUp(self):
        self.switch = DataCenterAssetFactory(hostname="sw1.example.com")
        self.server = DataCenterAssetFactory(hostname="srv1.example.com")
        self.extra_host = DataCenterAssetFactory(hostname="srv2.example.com")

        self.switch_port = Port.objects.create(
            label="Gi0/1", data_center_asset=self.switch
        )
        self.server_port = Port.objects.create(
            label="eth0", data_center_asset=self.server
        )
        self.server_backup_port = Port.objects.create(
            label="eth1", data_center_asset=self.server
        )
        self.extra_port = Port.objects.create(
            label="eth1", data_center_asset=self.extra_host
        )
        self.extra_port_deep = Port.objects.create(
            label="eth2", data_center_asset=self.extra_host
        )

        self.connection = Connection.objects.create()
        ConnectionMember.objects.create(
            connection=self.connection, port=self.switch_port
        )
        ConnectionMember.objects.create(
            connection=self.connection, port=self.server_port
        )

        self.extra_connection = Connection.objects.create()
        ConnectionMember.objects.create(
            connection=self.extra_connection, port=self.server_backup_port
        )
        ConnectionMember.objects.create(
            connection=self.extra_connection, port=self.extra_port
        )

        # Third hop chain for depth tests: sw1 -> srv1 -> srv2 -> srv3
        self.deep_host = DataCenterAssetFactory(hostname="srv3.example.com")
        self.deep_port = Port.objects.create(
            label="eth9", data_center_asset=self.deep_host
        )
        self.deep_connection = Connection.objects.create()
        ConnectionMember.objects.create(
            connection=self.deep_connection, port=self.extra_port_deep
        )
        ConnectionMember.objects.create(
            connection=self.deep_connection, port=self.deep_port
        )

    def test_command_outputs_mermaid_graph(self):
        out = StringIO()

        call_command("generate_switchport_graph", stdout=out)

        output = out.getvalue()
        self.assertIn("graph LR", output)
        self.assertIn("sw1.example.com", output)
        self.assertIn("srv1.example.com", output)
        self.assertNotIn("sw1.example.com<br/>Gi0/1", output)
        self.assertTrue("Gi0/1" in output and "eth0" in output)
        switch_id = f"asset_{self.switch.pk}"
        server_id = f"asset_{self.server.pk}"
        expected_edges = {
            f'{switch_id} <-->|"Gi0/1 ↔ eth0"| {server_id}',
            f'{server_id} <-->|"eth0 ↔ Gi0/1"| {switch_id}',
        }
        self.assertTrue(any(edge in output for edge in expected_edges))

    def test_same_hostname_single_node(self):
        out = StringIO()

        call_command("generate_switchport_graph", stdout=out)

        output = out.getvalue()
        self.assertEqual(output.count(f'asset_{self.server.pk}["srv1.example.com"]'), 1)

    def test_command_filters_connections_by_hostname(self):
        out = StringIO()

        call_command(
            "generate_switchport_graph",
            "--hostname=srv2.example.com",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("srv2.example.com", output)
        self.assertIn("eth1", output)
        self.assertNotIn("sw1.example.com", output)
        self.assertNotIn("Gi0/1", output)

    def test_depth_1_only_direct_neighbors(self):
        out = StringIO()

        call_command(
            "generate_switchport_graph",
            "--hostname=sw1.example.com",
            "--depth=1",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("sw1.example.com", output)
        self.assertIn("srv1.example.com", output)
        self.assertIn("Gi0/1", output)
        self.assertIn("eth0", output)
        self.assertNotIn("srv2.example.com", output)
        self.assertNotIn("srv3.example.com", output)

    def test_depth_2_includes_neighbors_of_neighbors(self):
        out = StringIO()

        call_command(
            "generate_switchport_graph",
            "--hostname=sw1.example.com",
            "--depth=2",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("srv2.example.com", output)
        self.assertIn("eth1", output)
        self.assertNotIn("srv3.example.com", output)

    def test_depth_3_includes_third_hop(self):
        out = StringIO()

        call_command(
            "generate_switchport_graph",
            "--hostname=sw1.example.com",
            "--depth=3",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("srv3.example.com", output)
        self.assertIn("eth9", output)

    def test_rejects_invalid_depth(self):
        with self.assertRaises(CommandError):
            call_command("generate_switchport_graph", "--depth=0")

    def test_command_writes_graph_to_file(self):
        with TemporaryDirectory() as tmp_dir:
            output_path = f"{tmp_dir}/switchports.mmd"
            out = StringIO()

            call_command(
                "generate_switchport_graph",
                f"--output={output_path}",
                stdout=out,
            )

            with open(output_path, encoding="utf-8") as graph_file:
                saved_output = graph_file.read()

        self.assertIn("Saved graph to", out.getvalue())
        self.assertIn("graph LR", saved_output)


class PortLabelForSwitchTestCase(TestCase):
    def test_simple_number_becomes_0_0_prefix(self):
        self.assertEqual(_port_label_for_switch("20"), "0/0/20")

    def test_full_label_with_slashes_passes_through(self):
        self.assertEqual(_port_label_for_switch("1/0/5"), "1/0/5")

    def test_strips_whitespace(self):
        self.assertEqual(_port_label_for_switch("  20  "), "0/0/20")


class RackSwitchportGridViewTestCase(TestCase):
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

        self.rack_config = RackConfiguration.objects.create(rack=self.rack)
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

    def _make_view(self):
        """Create a view instance with self.object set."""
        view = RackSwitchportGridView()
        view.object = self.rack_config
        return view

    def test_get_rack_assets_returns_assets_in_rack(self):
        view = self._make_view()
        assets = list(view._get_rack_assets())
        hostnames = [a.hostname for a in assets]
        self.assertIn("srv1.example.com", hostnames)
        self.assertIn("srv2.example.com", hostnames)

    def test_get_switch_configs_returns_all_configs(self):
        view = self._make_view()
        configs = list(view._get_switch_configs())
        labels = [c.label for c in configs]
        self.assertEqual(sorted(labels), ["eth1", "eth2", "mgmt"])

    def test_build_connection_map_empty_when_no_connections(self):
        view = self._make_view()
        assets = list(view._get_rack_assets())
        switch_configs = list(view._get_switch_configs())
        connection_map = view._build_connection_map(assets, switch_configs)
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

        view = self._make_view()
        assets = list(view._get_rack_assets())
        switch_configs = list(view._get_switch_configs())
        connection_map = view._build_connection_map(assets, switch_configs)

        key = (self.server1.id, self.sc_eth1.id)
        self.assertIn(key, connection_map)
        self.assertEqual(connection_map[key]["switch_port_label"], "0/0/20")
        self.assertEqual(connection_map[key]["asset_port_label"], "eth1")

    def test_grid_rows_built_correctly(self):
        """Test the grid row building logic without going through full view."""
        view = self._make_view()
        assets = list(view._get_rack_assets())
        switch_configs = list(view._get_switch_configs())
        connection_map = view._build_connection_map(assets, switch_configs)

        # Build rows the same way the view does
        rows = []
        for asset in assets:
            cells = []
            for sc in switch_configs:
                conn_info = connection_map.get((asset.id, sc.id))
                if conn_info:
                    switch_port_label = conn_info["switch_port_label"]
                    display_value = switch_port_label
                    if switch_port_label.startswith("0/0/"):
                        display_value = switch_port_label[4:]
                else:
                    display_value = ""
                cells.append(
                    {
                        "switch_config": sc,
                        "value": display_value,
                        "field_name": f"port_{asset.id}_{sc.id}",
                    }
                )
            rows.append({"asset": asset, "cells": cells})

        # 3 switch configs -> 3 cells per row
        for row in rows:
            self.assertEqual(len(row["cells"]), 3)
        # 2 assets in the rack -> 2 rows
        self.assertEqual(len(rows), 2)

    def test_grid_shows_existing_port_number(self):
        # Connect server1:eth1 <-> switch_eth1:0/0/42
        asset_port = Port.objects.create(label="eth1", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="0/0/42", data_center_asset=self.switch_eth1
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        view = self._make_view()
        assets = list(view._get_rack_assets())
        switch_configs = list(view._get_switch_configs())
        connection_map = view._build_connection_map(assets, switch_configs)

        conn_info = connection_map.get((self.server1.id, self.sc_eth1.id))
        self.assertIsNotNone(conn_info)
        # "0/0/42" -> display as "42"
        switch_port_label = conn_info["switch_port_label"]
        if switch_port_label.startswith("0/0/"):
            display_value = switch_port_label[4:]
        else:
            display_value = switch_port_label
        self.assertEqual(display_value, "42")

    def test_nonstandard_port_label_passes_through(self):
        """Port labels like '1/0/5' are not stripped."""
        asset_port = Port.objects.create(label="eth2", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="1/0/5", data_center_asset=self.switch_eth2
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        view = self._make_view()
        assets = list(view._get_rack_assets())
        switch_configs = list(view._get_switch_configs())
        connection_map = view._build_connection_map(assets, switch_configs)

        conn_info = connection_map.get((self.server1.id, self.sc_eth2.id))
        self.assertIsNotNone(conn_info)
        self.assertEqual(conn_info["switch_port_label"], "1/0/5")


def _make_interface(name, remote_name="", remote_id=None, remote_port=None, desc=""):
    """Helper to create an InterfaceDTO for testing."""
    return InterfaceDTO(
        name=name,
        name_cfg=f"xe-{name}",
        speed=10000,
        desc=desc,
        uplink=False,
        status=InterfaceStatus.UP,
        admin_status=InterfaceStatus.UP,
        interface_mode=InterfaceMode.ACCESS,
        remote_name=remote_name,
        remote_id=remote_id,
        remote_port=remote_port,
        mtu="9216",
    )


class RefreshValidationTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-Validation")
        self.switch = DataCenterAssetFactory(hostname="sw1.dc.example.com")
        self.server = DataCenterAssetFactory(
            hostname="srv1.dc.example.com", rack=self.rack, position=10
        )
        self.rack_config = RackConfiguration.objects.create(rack=self.rack)
        self.sc_eth1 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch,
            label="eth1",
        )

    @patch("ralph.switchports.validation.NetmakerSwitchportBackend")
    def test_refresh_creates_validation_results(self, MockBackend):
        switch_dto = SwitchDTO(
            hostname="sw1.dc.example.com",
            sn="SN123",
            barcode="BC123",
            model="TestModel",
            ansible_unify_model="test",
            acs_device_type="vendor#TestVendor",
            ralph_id=self.switch.id,
            location_rack="TestRack",
            location_dc="DC1",
            location_position=44,
            ports=[
                _make_interface(
                    "0/0/10",
                    remote_name="srv1.dc.example.com",
                ),
                _make_interface("0/0/11", remote_name=""),
            ],
        )
        MockBackend.return_value.get_switchports.return_value = switch_dto

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["refreshed_switches"], 1)
        self.assertEqual(summary["ports_processed"], 2)

        # Port 0/0/10 should find server1
        result = BackendValidationResult.objects.get(
            rack_configuration=self.rack_config,
            switch=self.switch,
            port_label="0/0/10",
        )
        self.assertEqual(result.status, ValidationStatus.ASSET_FOUND)
        self.assertEqual(result.remote_asset, self.server)
        self.assertEqual(result.remote_hostname, "srv1.dc.example.com")

        # Port 0/0/11 has no remote - PORT_NOT_FOUND
        result_empty = BackendValidationResult.objects.get(
            rack_configuration=self.rack_config,
            switch=self.switch,
            port_label="0/0/11",
        )
        self.assertEqual(result_empty.status, ValidationStatus.PORT_NOT_FOUND)

    @patch("ralph.switchports.validation.NetmakerSwitchportBackend")
    def test_refresh_switch_not_found(self, MockBackend):
        MockBackend.return_value.get_switchports.side_effect = Exception("Not found")

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["switch_not_found"], 1)
        result = BackendValidationResult.objects.get(
            rack_configuration=self.rack_config,
            switch=self.switch,
            port_label="__switch__",
        )
        self.assertEqual(result.status, ValidationStatus.SWITCH_NOT_FOUND)

    @patch("ralph.switchports.validation.NetmakerSwitchportBackend")
    def test_refresh_replaces_old_results(self, MockBackend):
        # Create old result
        BackendValidationResult.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch,
            port_label="0/0/99",
            status=ValidationStatus.ASSET_FOUND,
            remote_hostname="old.example.com",
        )

        switch_dto = SwitchDTO(
            hostname="sw1.dc.example.com",
            sn="SN123",
            barcode="BC123",
            model="TestModel",
            ansible_unify_model="test",
            acs_device_type="vendor#TestVendor",
            ralph_id=self.switch.id,
            location_rack="TestRack",
            location_dc="DC1",
            location_position=44,
            ports=[_make_interface("0/0/10", remote_name="srv1.dc.example.com")],
        )
        MockBackend.return_value.get_switchports.return_value = switch_dto

        refresh_validation_for_rack(self.rack_config)

        # Old result should be gone
        self.assertFalse(
            BackendValidationResult.objects.filter(port_label="0/0/99").exists()
        )
        # New result should exist
        self.assertTrue(
            BackendValidationResult.objects.filter(port_label="0/0/10").exists()
        )
