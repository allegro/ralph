from django.test import TestCase

from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterFactory,
    RackFactory,
    ServerRoomFactory,
)
from ralph.switchports.rackconfig.switch_resolver import resolve_switch


class ResolveSwitchTestCase(TestCase):
    def setUp(self):
        self.dc = DataCenterFactory(name="DC-resolve")
        self.server_room = ServerRoomFactory(name="SR-resolve", data_center=self.dc)
        self.rack = RackFactory(name="Rack 12", server_room=self.server_room)
        self.switch = DataCenterAssetFactory(
            hostname="resolve.sw.local",
            barcode="RSW-BC-1",
            rack=self.rack,
            position=42,
        )

    def test_resolve_by_barcode(self):
        self.assertEqual(resolve_switch("RSW-BC-1"), self.switch)

    def test_resolve_by_hostname(self):
        self.assertEqual(resolve_switch("resolve.sw.local"), self.switch)

    def test_resolve_by_rack_position(self):
        self.assertEqual(resolve_switch("rack12u42", self.dc), self.switch)

    def test_resolve_rack_position_strips_whitespace(self):
        self.assertEqual(resolve_switch("  rack12u42 ", self.dc), self.switch)

    def test_rack_position_requires_dc_context(self):
        # Without a data center the position format must not be attempted.
        self.assertIsNone(resolve_switch("rack12u42"))

    def test_rack_position_unknown_returns_none(self):
        self.assertIsNone(resolve_switch("rack12u99", self.dc))

    def test_unknown_identifier_returns_none(self):
        self.assertIsNone(resolve_switch("nope-nothing", self.dc))

    def test_blank_returns_none(self):
        self.assertIsNone(resolve_switch("   ", self.dc))
