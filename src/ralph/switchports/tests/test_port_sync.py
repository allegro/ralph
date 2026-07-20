from unittest.mock import patch

from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.models import (
    Connection,
    ConnectionMember,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
)
from ralph.switchports.sync.refresh import refresh_validation_for_rack
from ralph.switchports.tests.helpers import make_interface, make_switch_dto

BACKEND = "ralph.switchports.sync.refresh.NetmakerSwitchportBackend"


class SyncSwitchPortsTestCase(TestCase):
    """The switch is the source of truth for its ports; connected ports stay."""

    def setUp(self):
        self.rack = RackFactory(name="TestRack-PortSync")
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
    def test_refresh_creates_missing_switch_ports(self, MockBackend):
        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [
                make_interface("0/0/10", remote_name="srv1.dc.example.com"),
                make_interface("0/0/11", remote_name=""),
            ]
        )

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["switch_ports_created"], 2)
        self.assertEqual(
            set(
                Port.objects.filter(data_center_asset=self.switch).values_list(
                    "label", flat=True
                )
            ),
            {"0/0/10", "0/0/11"},
        )
        # No server ports may be created by the refresh.
        self.assertFalse(Port.objects.filter(data_center_asset=self.server).exists())

    @patch(BACKEND)
    def test_refresh_deletes_vanished_switch_ports(self, MockBackend):
        # Port that the backend will no longer report.
        Port.objects.create(label="0/0/99", data_center_asset=self.switch)
        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [make_interface("0/0/10", remote_name="srv1.dc.example.com")]
        )

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary["switch_ports_deleted"], 1)
        self.assertEqual(
            set(
                Port.objects.filter(data_center_asset=self.switch).values_list(
                    "label", flat=True
                )
            ),
            {"0/0/10"},
        )

    @patch(BACKEND)
    def test_refresh_keeps_existing_switch_ports(self, MockBackend):
        existing = Port.objects.create(label="0/0/10", data_center_asset=self.switch)
        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [make_interface("0/0/10", remote_name="srv1.dc.example.com")]
        )

        summary = refresh_validation_for_rack(self.rack_config)

        self.assertEqual(summary.get("switch_ports_created", 0), 0)
        self.assertEqual(summary.get("switch_ports_deleted", 0), 0)
        ports = Port.objects.filter(data_center_asset=self.switch)
        self.assertEqual(ports.count(), 1)
        self.assertEqual(ports.first().id, existing.id)

    @patch(BACKEND)
    def test_connected_switch_port_is_kept_even_if_backend_drops_it(self, MockBackend):
        switch_port = Port.objects.create(label="0/0/99", data_center_asset=self.switch)
        server_port = Port.objects.create(label="eth1", data_center_asset=self.server)
        connection = Connection.objects.create()
        ConnectionMember.objects.create(connection=connection, port=switch_port)
        ConnectionMember.objects.create(connection=connection, port=server_port)

        # Backend no longer reports 0/0/99, but the port still has a connection,
        # so it (and its connection) must be preserved.
        MockBackend.return_value.get_switchports.return_value = self._switch_dto(
            [make_interface("0/0/10", remote_name="srv1.dc.example.com")]
        )

        summary = refresh_validation_for_rack(self.rack_config)

        # The connected switch port is not counted as deleted...
        self.assertEqual(summary.get("switch_ports_deleted", 0), 0)
        # ...and everything survives: both ports, the connection and its members.
        self.assertTrue(Port.objects.filter(id=switch_port.id).exists())
        self.assertTrue(Port.objects.filter(id=server_port.id).exists())
        self.assertTrue(Connection.objects.filter(id=connection.id).exists())
        self.assertEqual(ConnectionMember.objects.count(), 2)
