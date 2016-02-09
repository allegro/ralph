# -*- coding: utf-8 -*-
import factory
from django.core.exceptions import ValidationError

from ralph.assets.models.choices import ObjectModelType
from ralph.assets.tests.factories import (
    CategoryFactory,
    DataCenterAssetModelFactory,
    ManufacturerFactory
)
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.licences.models import BaseObjectLicence
from ralph.licences.tests.factories import (
    LicenceFactory,
    LicenceWithUserAndBaseObjectsFactory
)
from ralph.reports.models import ReportLanguage
from ralph.reports.views import (
    AssetRelationsReport,
    CategoryModelReport,
    CategoryModelStatusReport,
    LicenceRelationsReport
)
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


class TestReportAssetAndLicence(RalphTestCase):
    def setUp(self):
        self.model = DataCenterAssetModelFactory(
            category=CategoryFactory(name="Keyboard"),
            type=ObjectModelType.data_center,
            name='Keyboard1',
            manufacturer=ManufacturerFactory(name='M1')
        )
        self.dc_1 = DataCenterAssetFactory(
            force_depreciation=False,
            model=self.model,
        )
        self.licence = LicenceFactory(
            number_bought=1,
            niw='N/A',
            software__name='Project Info',
            software__asset_type=ObjectModelType.data_center
        )
        BaseObjectLicence.objects.create(
            licence=self.licence, base_object=self.dc_1.baseobject_ptr
        )

    def test_asset_relation(self):
        asset_relation = AssetRelationsReport()
        report_result = list(asset_relation.prepare(DataCenterAsset))
        result = [
            [
                'id', 'niw', 'barcode', 'sn', 'model__category__name',
                'model__manufacturer__name', 'status',
                'service_env__service__name', 'invoice_date', 'invoice_no',
                'hostname'
            ],
            [
                str(self.dc_1.id), '', self.dc_1.barcode, self.dc_1.sn,
                'Keyboard', 'M1', '1', 'None', str(self.dc_1.invoice_date),
                str(self.dc_1.invoice_no), self.dc_1.hostname
            ]
        ]
        self.assertEqual(report_result, result)

    def test_num_queries_dc(self):
        licence_relation = LicenceRelationsReport()
        with self.assertNumQueries(3):
            list(licence_relation.prepare(
                DataCenterAsset)
            )

    def test_num_queries_bo(self):
        factory.build_batch(LicenceWithUserAndBaseObjectsFactory, 100)
        licence_relation = LicenceRelationsReport()
        with self.assertNumQueries(3):
            list(licence_relation.prepare(
                BackOfficeAsset)
            )

    def test_licence_relation(self):
        licence_relation = LicenceRelationsReport()
        report_result = list(licence_relation.prepare(
            DataCenterAsset)
        )
        result = [
            [
                'niw', 'software', 'number_bought', 'price', 'invoice_date',
                'invoice_no', 'id', 'asset__barcode', 'asset__niw',
                'asset__backofficeasset__user__username',
                'asset__backofficeasset__user__first_name',
                'asset__backofficeasset__user__last_name',
                'asset__backofficeasset__owner__username',
                'asset__backofficeasset__owner__first_name',
                'asset__backofficeasset__owner__last_name',
                'asset__backofficeasset__region__name', 'user__username',
                'user__first_name', 'user__last_name', 'single_cost'
            ],
            [
                'N/A', 'Project Info', '1', '0.00',
                str(self.licence.invoice_date), str(self.licence.invoice_no),
                '', '', '', '', '', '', '', '', '', '', '', '', '', ''
            ],
            [
                'N/A', 'Project Info', '1', '0.00',
                str(self.licence.invoice_date), str(self.licence.invoice_no),
                str(self.dc_1.id), self.dc_1.asset.barcode,
                '', 'None', 'None', 'None', 'None', 'None', 'None', 'None',
                '', '', '', ''
            ]
        ]

        self.assertEqual(report_result, result)


class TestReportLanguage(RalphTestCase):

    def test_clean_metod(self):
        ReportLanguage.objects.create(name='pl', default=True)
        lang_2 = ReportLanguage.objects.create(name='en', default=False)

        with self.assertRaisesRegex(
            ValidationError,
            (
                'Only one language can be default.'
            )
        ):
            lang_2.default = True
            lang_2.clean()
