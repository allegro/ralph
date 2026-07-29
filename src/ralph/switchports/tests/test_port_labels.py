from django.test import TestCase

from ralph.switchports.rackconfig.port_labels import to_display, to_switch_label


class ToSwitchLabelTestCase(TestCase):
    def test_simple_number_becomes_0_0_prefix(self):
        self.assertEqual(to_switch_label("20"), "0/0/20")

    def test_full_label_with_slashes_passes_through(self):
        self.assertEqual(to_switch_label("1/0/5"), "1/0/5")

    def test_strips_whitespace(self):
        self.assertEqual(to_switch_label("  20  "), "0/0/20")


class ToDisplayTestCase(TestCase):
    def test_strips_default_prefix(self):
        self.assertEqual(to_display("0/0/42"), "42")

    def test_nonstandard_label_passes_through(self):
        self.assertEqual(to_display("1/0/5"), "1/0/5")
