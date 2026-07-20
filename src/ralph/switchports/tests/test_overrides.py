from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports import grid
from ralph.switchports.models import (
    BackendValidationResult,
    Connection,
    ConnectionMember,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
    RackSwitchConfigurationOverride,
    ValidationStatus,
)
from ralph.switchports.rackconfig.overrides import build_override_map, effective_switch
from ralph.switchports.sync.switches import iter_rack_switches


class SwitchOverrideTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-Override")
        self.switch_eth1 = DataCenterAssetFactory(hostname="ovr.sw.eth1.local")
        self.switch_alt = DataCenterAssetFactory(
            hostname="ovr.sw.alt.local", barcode="ALT-BC-1"
        )
        self.server1 = DataCenterAssetFactory(
            hostname="ovr-srv1.example.com", rack=self.rack, position=1
        )
        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        self.sc_eth1 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_eth1,
            label="eth1",
        )

    def test_effective_switch_defaults_to_column_switch(self):
        override_map = build_override_map([self.sc_eth1])
        self.assertEqual(
            effective_switch(self.sc_eth1, self.server1.id, override_map),
            self.switch_eth1,
        )

    def test_effective_switch_uses_override(self):
        RackSwitchConfigurationOverride.objects.create(
            rack_switch_configuration=self.sc_eth1,
            data_center_asset=self.server1,
            switch=self.switch_alt,
        )
        override_map = build_override_map([self.sc_eth1])
        self.assertEqual(
            effective_switch(self.sc_eth1, self.server1.id, override_map),
            self.switch_alt,
        )

    def test_connection_map_recognizes_override_switch(self):
        # server1:eth1 physically connected to the ALTERNATE switch
        RackSwitchConfigurationOverride.objects.create(
            rack_switch_configuration=self.sc_eth1,
            data_center_asset=self.server1,
            switch=self.switch_alt,
        )
        asset_port = Port.objects.create(label="eth1", data_center_asset=self.server1)
        switch_port = Port.objects.create(
            label="0/0/7", data_center_asset=self.switch_alt
        )
        conn = Connection.objects.create()
        ConnectionMember.objects.create(connection=conn, port=asset_port)
        ConnectionMember.objects.create(connection=conn, port=switch_port)

        assets = list(grid.get_rack_assets(self.rack))
        switch_configs = list(grid.get_switch_configs(self.rack_config))
        connection_map = grid.build_connection_map(assets, switch_configs)

        key = (self.server1.id, self.sc_eth1.id)
        self.assertIn(key, connection_map)
        self.assertEqual(connection_map[key]["actual_switch_id"], self.switch_alt.id)
        self.assertEqual(connection_map[key]["switch_port_label"], "0/0/7")

    def test_iter_rack_switches_includes_overrides(self):
        RackSwitchConfigurationOverride.objects.create(
            rack_switch_configuration=self.sc_eth1,
            data_center_asset=self.server1,
            switch=self.switch_alt,
        )
        switches = iter_rack_switches(self.rack_config)
        ids = {s.id for s in switches}
        self.assertEqual(ids, {self.switch_eth1.id, self.switch_alt.id})

    def test_client_validation_excludes_overrides_and_disabled(self):
        switch_configs = list(grid.get_switch_configs(self.rack_config))
        # a validation result on the default switch
        BackendValidationResult.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch_eth1,
            port_label="0/0/5",
            status=ValidationStatus.ASSET_FOUND,
            remote_asset=self.server1,
            remote_hostname="ovr-srv1.example.com",
        )
        validation_map, switch_status = grid.build_validation_map(self.rack_config)
        client = grid.build_client_validation(
            switch_configs, validation_map, switch_status
        )
        self.assertIn(str(self.sc_eth1.id), client)
        self.assertIn("0/0/5", client[str(self.sc_eth1.id)]["ports"])

        # disabling backend validation drops the column from client data
        self.sc_eth1.backend_validation = False
        self.sc_eth1.save()
        switch_configs = list(grid.get_switch_configs(self.rack_config))
        validation_map, switch_status = grid.build_validation_map(self.rack_config)
        client = grid.build_client_validation(
            switch_configs, validation_map, switch_status
        )
        self.assertNotIn(str(self.sc_eth1.id), client)
