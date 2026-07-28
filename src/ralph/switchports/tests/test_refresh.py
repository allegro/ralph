from unittest.mock import patch

from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    RackSwitchConfiguration,
    ValidationStatus,
)
from ralph.switchports.sync.refresh import refresh_validation_for_rack
from ralph.switchports.tests.helpers import make_interface, make_switch_dto

BACKEND = "ralph.switchports.sync.refresh.NetmakerSwitchportBackend"


class RefreshValidationTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-Validation")
        self.switch = DataCenterAssetFactory(hostname="sw1.dc.example.com")
        self.server = DataCenterAssetFactory(
            hostname="srv1.dc.example.com", rack=self.rack, position=10
        )
        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)
        self.sc_eth1 = RackSwitchConfiguration.objects.create(
            rack_configuration=self.rack_config,
            switch=self.switch,
            label="eth1",
        )

    def _switch_dto(self, ports):
        return make_switch_dto(self.switch.id, ports)

    @patch(BACKEND)
    def test_refresh_creates_validation_results(self, MockBackend):
        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [
                make_interface("0/0/10", remote_name="srv1.dc.example.com"),
                make_interface("0/0/11", remote_name=""),
            ]
        )

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["refreshed_switches"], 1)
        self.assertEqual(summary["ports_processed"], 2)

        # Port 0/0/10 should find server1
        result = BackendValidationResult.objects.get(
            switch=self.switch,
            port_label="0/0/10",
        )
        self.assertEqual(result.status, ValidationStatus.ASSET_FOUND)
        self.assertEqual(result.remote_asset, self.server)
        self.assertEqual(result.remote_hostname, "srv1.dc.example.com")

        # Port 0/0/11 has no remote - PORT_NOT_FOUND
        result_empty = BackendValidationResult.objects.get(
            switch=self.switch,
            port_label="0/0/11",
        )
        self.assertEqual(result_empty.status, ValidationStatus.PORT_NOT_FOUND)

    @patch(BACKEND)
    def test_refresh_skips_switch_with_backend_validation_disabled(self, MockBackend):
        # Stale result that should be cleaned up once validation is disabled
        BackendValidationResult.objects.create(
            switch=self.switch,
            port_label="0/0/10",
            status=ValidationStatus.ASSET_FOUND,
            remote_hostname="stale.example.com",
        )
        self.sc_eth1.backend_validation = False
        self.sc_eth1.save()

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["skipped_switches"], 1)
        self.assertEqual(summary["refreshed_switches"], 0)
        # Backend must not be queried for a disabled switch
        MockBackend.return_value.get_switchports.assert_not_called()

    @patch(BACKEND)
    def test_refresh_switch_not_found(self, MockBackend):
        MockBackend.return_value.get_switchports.side_effect = Exception("Not found")

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["switch_not_found"], 1)
        result = BackendValidationResult.objects.get(
            switch=self.switch,
            port_label="__switch__",
        )
        self.assertEqual(result.status, ValidationStatus.SWITCH_NOT_FOUND)

    @patch(BACKEND)
    def test_refresh_replaces_old_results(self, MockBackend):
        # Create old result
        BackendValidationResult.objects.create(
            switch=self.switch,
            port_label="0/0/99",
            status=ValidationStatus.ASSET_FOUND,
            remote_hostname="old.example.com",
        )

        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [make_interface("0/0/10", remote_name="srv1.dc.example.com")]
        )

        refresh_validation_for_rack(self.rack_config)

        # Old result should be gone
        self.assertFalse(
            BackendValidationResult.objects.filter(port_label="0/0/99").exists()
        )
        # New result should exist
        self.assertTrue(
            BackendValidationResult.objects.filter(port_label="0/0/10").exists()
        )
