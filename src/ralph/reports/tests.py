# -*- coding: utf-8 -*-

from ralph.assets.models.choices import ObjectModelType
from ralph.assets.tests.factories import (
    CategoryFactory,
    DataCenterAssetModelFactory
)
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.reports.views import CategoryModelReport, CategoryModelStatusReport
from ralph.tests import RalphTestCase
from ralph.tests.mixins import ClientMixin


class TestReportCategoryTreeView(ClientMixin, RalphTestCase):

    def setUp(self):
        self.client = self.login_as_user()
        self._create_models()
        self._create_assets()

    def _create_models(self):
        self.keyboard_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Keyboard"),
            type=ObjectModelType.data_center,
            name='Keyboard1',
        )
        self.mouse_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Mouse"),
            type=ObjectModelType.data_center,
            name='Mouse1',
        )
        self.pendrive_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Pendrive"),
            type=ObjectModelType.data_center,
            name='Pendrive1',
        )

        self.model_monitor = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Monitor"),
            type=ObjectModelType.data_center,
            name='Monitor1',
        )
        self.navigation_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Navigation"),
            type=ObjectModelType.data_center,
            name='Navigation1',
        )
        self.scanner_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Scanner"),
            type=ObjectModelType.data_center,
            name='Scanner1',
        )
        self.shredder_model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Shredder"),
            type=ObjectModelType.data_center,
            name='Shredder1',
        )

    def _create_assets(self):
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.keyboard_model
        }) for _ in range(6)]
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.mouse_model
        }) for _ in range(2)]
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.pendrive_model
        }) for _ in range(2)]

        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.model_monitor
        }) for _ in range(2)]
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.navigation_model
        }) for _ in range(2)]
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.scanner_model
        }) for _ in range(3)]
        [DataCenterAssetFactory(**{
            'force_depreciation': False,
            'model': self.shredder_model
        }) for _ in range(3)]

    def _get_item(self, data, name):
        # import ipdb; ipdb.set_trace()
        for item in data:
            if item['name'] == name:

                return item
        return None

    def _get_report(self, report_class, mode=None):
        report = report_class()
        report.execute(DataCenterAsset)
        return report.report.to_dict()

    def test_category_model_tree(self):
        report = self._get_report(CategoryModelReport)

        self.assertEqual(self._get_item(report, 'Keyboard')['count'], 6)
        self.assertEqual(self._get_item(report, 'Mouse')['count'], 2)
        self.assertEqual(self._get_item(report, 'Pendrive')['count'], 2)

        self.assertEqual(self._get_item(report, 'Monitor')['count'], 2)
        self.assertEqual(self._get_item(report, 'Navigation')['count'], 2)
        self.assertEqual(self._get_item(report, 'Scanner')['count'], 3)
        self.assertEqual(self._get_item(report, 'Shredder')['count'], 3)

    def test_category_model_status_tree(self):
        report = self._get_report(CategoryModelStatusReport)

        item = self._get_item(report, 'Keyboard')['children'][0]['children']
        self.assertEqual(item[0]['count'], 6)
        item = self._get_item(report, 'Mouse')['children'][0]['children']
        self.assertEqual(item[0]['count'], 2)
        item = self._get_item(report, 'Pendrive')['children'][0]['children']
        self.assertEqual(item[0]['count'], 2)

        item = self._get_item(report, 'Monitor')['children'][0]['children']
        self.assertEqual(item[0]['count'], 2)
        item = self._get_item(report, 'Navigation')['children'][0]['children']
        self.assertEqual(item[0]['count'], 2)
        item = self._get_item(report, 'Scanner')['children'][0]['children']
        self.assertEqual(item[0]['count'], 3)
        item = self._get_item(report, 'Shredder')['children'][0]['children']
        self.assertEqual(item[0]['count'], 3)
