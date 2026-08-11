from django.test import TestCase

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    ValidationStatus,
)
from ralph.switchports.presentation import (
    build_validation_context,
    format_speed,
    status_symbol,
)


class BuildValidationContextTestCase(TestCase):
    def setUp(self):
        self.rack = RackFactory(name="TestRack-Presentation")
        self.switch = DataCenterAssetFactory(hostname="sw-pres.dc.example.com")
        self.server = DataCenterAssetFactory(hostname="srv-pres.dc.example.com")
        self.rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.rack)

    def _make_vr(self, **kwargs):
        defaults = {
            "switch": self.switch,
            "port_label": "0/0/10",
            "status": ValidationStatus.ASSET_FOUND,
            "remote_asset": self.server,
            "remote_hostname": "srv-pres.dc.example.com",
            "oper_status": "up",
            "admin_status": "up",
            "speed": 25000,
            "raw_data": {"name": "0/0/10", "speed": 25000},
        }
        defaults.update(kwargs)
        return BackendValidationResult.objects.create(**defaults)

    def test_none_returns_none(self):
        self.assertIsNone(build_validation_context(None, expected_asset_id=1))

    def test_asset_found_match(self):
        vr = self._make_vr()
        ctx = build_validation_context(vr, expected_asset_id=self.server.id)
        self.assertTrue(ctx["match"])
        self.assertEqual(ctx["css_class"], "validation-ok")
        self.assertEqual(ctx["oper_symbol"], "\u2191")
        self.assertEqual(ctx["admin_symbol"], "\u2191")
        self.assertEqual(ctx["speed_display"], "25G")
        self.assertIn("0/0/10", ctx["raw_json"])

    def test_asset_found_mismatch(self):
        vr = self._make_vr()
        ctx = build_validation_context(vr, expected_asset_id=self.server.id + 999)
        self.assertFalse(ctx["match"])
        self.assertEqual(ctx["css_class"], "validation-mismatch")

    def test_format_speed(self):
        self.assertEqual(format_speed(25000), "25G")
        self.assertEqual(format_speed(1000), "1G")
        self.assertEqual(format_speed(100), "100M")
        self.assertEqual(format_speed(None), "")

    def test_status_symbol(self):
        self.assertEqual(status_symbol("up"), "\u2191")
        self.assertEqual(status_symbol("down"), "\u2193")
        self.assertEqual(status_symbol("weird"), "?")
        self.assertEqual(status_symbol(""), "?")
