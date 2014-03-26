"""Tests for ralph UI reports"""
from django.test import TestCase

from ralph.ui.views.reports import _report_services_data_provider


class TestServices(TestCase):

    """Test for services reports."""

    fixtures = ['services_rel']

    def setUp(self):
        self.report = _report_services_data_provider()

    def test_invalid_report(self):
        self.assertEqual(len(self.report['invalid_relations']), 1)
        self.assertEqual(self.report['invalid_relations'][0].barcode, '00002')

    def test_no_venture_report(self):
        self.assertEqual(len(self.report['services_without_venture']), 2)
        self.assertSetEqual(
            set([
                report.barcode
                for report in self.report['services_without_venture']
                ]),
            {'00002', '00003'},
        )
