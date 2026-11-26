from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports import grid
from ralph.switchports.grid_edit import CellEdit, apply_cell_edit
from ralph.switchports.models import (
    Connection,
    ConnectionMember,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
    RackSwitchConfigurationOverride,
)


class ApplyCellEditTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-CellEdit")
        self.switch_eth1 = DataCenterAssetFactory(hostname="ce.sw.eth1.local")
        self.server1 = DataCenterAssetFactory(hostname="ce-srv1.local", rack=self.rack, position=1)
        self.server2 = DataCenterAssetFactory(hostname="ce-srv2.local", rack=self.rack, position=2)
        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        self.sc_eth1 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_eth1,
            label="eth1",
        )

    def _connection_map(self):
        assets = list(grid.get_rack_assets(self.rack))
        switch_configs = list(grid.get_switch_configs(self.rack_config))
        return grid.build_connection_map(assets, switch_configs)

    def _connect(self, server, switch, switch_label, server_label="eth1"):
        asset_port = Port.objects.create(label=server_label, data_center_asset=server)
        switch_port = Port.objects.create(label=switch_label, data_center_asset=switch)
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)
        return conn

    def _apply(self, asset, **kwargs):
        return apply_cell_edit(
            asset, self.sc_eth1, CellEdit(**kwargs), self._connection_map(), None
        )

    def test_connect_to_free_port(self):
        result = self._apply(self.server1, new_value="30")
        self.assertEqual(result.created, 1)
        self.assertIsNone(result.conflict)
        self.assertTrue(
            Port.objects.filter(label="0/0/30", data_center_asset=self.switch_eth1).exists()
        )

    def test_conflict_is_deferred_and_nothing_changes(self):
        # server2 already sits on 0/0/30.
        self._connect(self.server2, self.switch_eth1, "0/0/30")

        result = self._apply(self.server1, new_value="30")

        self.assertIsNotNone(result.conflict)
        self.assertEqual(result.created, 0)
        self.assertEqual(result.conflict["owner_hostname"], "ce-srv2.local")
        self.assertEqual(result.conflict["switch_port_label"], "0/0/30")
        self.assertEqual(result.conflict["typed_value"], "30")
        # server1 got no port/connection on the switch.
        self.assertFalse(
            Port.objects.filter(label="eth1", data_center_asset=self.server1).exists()
        )
        # server2 keeps its connection.
        self.assertEqual(ConnectionMember.objects.count(), 2)

    def test_forced_overwrite_steals_the_port(self):
        conn = self._connect(self.server2, self.switch_eth1, "0/0/30")

        result = self._apply(self.server1, new_value="30", forced=True)

        self.assertEqual(result.created, 1)
        self.assertIsNone(result.conflict)
        # The old connection is gone, server1 now owns 0/0/30.
        self.assertFalse(Connection.objects.filter(id=conn.id).exists())
        switch_port = Port.objects.get(label="0/0/30", data_center_asset=self.switch_eth1)
        member = switch_port.connectionmember
        peers = {m.port.data_center_asset_id for m in member.connection.members.all()}
        self.assertIn(self.server1.id, peers)
        self.assertNotIn(self.server2.id, peers)

    def test_moving_own_port_is_not_a_conflict(self):
        # server1 already on 0/0/20; move it to a free 0/0/30.
        self._connect(self.server1, self.switch_eth1, "0/0/20")

        result = self._apply(self.server1, new_value="30")

        self.assertEqual(result.created, 1)
        self.assertIsNone(result.conflict)
        # eth1 now points at 0/0/30, old 0/0/20 connection is gone.
        eth1 = Port.objects.get(label="eth1", data_center_asset=self.server1)
        peer_labels = {m.port.label for m in eth1.connectionmember.connection.members.all()}
        self.assertIn("0/0/30", peer_labels)

    def test_clearing_cell_disconnects(self):
        self._connect(self.server1, self.switch_eth1, "0/0/20")

        result = self._apply(self.server1, new_value="")

        self.assertEqual(result.removed, 1)
        self.assertEqual(Connection.objects.count(), 0)

    def test_unchanged_cell_is_noop(self):
        self._connect(self.server1, self.switch_eth1, "0/0/20")

        result = self._apply(self.server1, new_value="20")

        self.assertEqual(result.created, 0)
        self.assertEqual(result.removed, 0)
        self.assertIsNone(result.conflict)

    def test_unknown_override_switch_is_error(self):
        result = self._apply(self.server1, new_value="30", override_value="does-not-exist")
        self.assertIsNotNone(result.error)
        self.assertIn("unknown switch", result.error)

    def test_override_to_alt_switch_is_persisted(self):
        alt = DataCenterAssetFactory(hostname="ce.sw.alt.local", barcode="ALT-CE-1")
        result = self._apply(self.server1, new_value="7", override_value="ALT-CE-1")
        self.assertEqual(result.created, 1)
        self.assertTrue(
            RackSwitchConfigurationOverride.objects.filter(
                rack_switch_configuration=self.sc_eth1,
                data_center_asset=self.server1,
                switch=alt,
            ).exists()
        )
        self.assertTrue(Port.objects.filter(label="0/0/7", data_center_asset=alt).exists())

    def test_empty_override_removes_existing_override(self):
        alt = DataCenterAssetFactory(hostname="ce.sw.alt.local", barcode="ALT-CE-1")
        self._apply(self.server1, new_value="7", override_value="ALT-CE-1")

        result = self._apply(self.server1, new_value="7", override_value="")

        self.assertIsNone(result.error)
        self.assertFalse(
            RackSwitchConfigurationOverride.objects.filter(
                rack_switch_configuration=self.sc_eth1,
                data_center_asset=self.server1,
            ).exists()
        )
        self.assertTrue(Port.objects.filter(label="0/0/7", data_center_asset=alt).exists())
