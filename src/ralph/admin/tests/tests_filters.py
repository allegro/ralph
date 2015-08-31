# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from ralph.admin.filters import (
    BooleanFilter,
    ChoicesFilter,
    date_format_to_human,
    DateFilter,
    TextFilter
)
from ralph.assets.models.choices import AssetStatus
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory


class InvoiceDateFilter(DateFilter):
    title = 'Invoice date'
    parameter_name = 'invoice_date'
    parameter_name_start = 'invoice_date_start'
    parameter_name_end = 'invoice_date_end'


class BarcodeFilter(TextFilter):
    title = 'Barcode'
    parameter_name = 'barcode'


class AdminFiltersTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dca_1 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 1, 1),
            barcode='barcode_one',
        )
        cls.dca_2 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 2, 1),
            barcode='barcode_two'
        )
        cls.dca_3 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 3, 1),
            force_depreciation=True
        )

    def test_date_format_to_human(self):
        self.assertEqual('YYYY-MM-DD', date_format_to_human('%Y-%m-%d'))
        self.assertEqual('YY-DD-MM', date_format_to_human('%y-%d-%m'))

    def test_boolean_filter(self):
        class ForceDepreciationFilter(BooleanFilter):
            title = 'Force depreciation'
            parameter_name = 'force_depreciation'

        boolean_filter = ForceDepreciationFilter(
            request=None,
            params={'force_depreciation': True},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = boolean_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_3.pk, queryset.first().pk)

    def test_choices_filter(self):
        class StatusFilter(ChoicesFilter):
            title = 'Status'
            parameter_name = 'status'
            choices_list = AssetStatus()

        choices_filter = StatusFilter(
            request=None,
            params={'status': AssetStatus.new},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(3, queryset.count())

        choices_filter = StatusFilter(
            request=None,
            params={'status': AssetStatus.in_progress},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(0, queryset.count())

    def test_text_filter(self):
        text_filter = BarcodeFilter(
            request=None,
            params={'barcode': 'barcode_one'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_text_filter_with_separator(self):
        text_filter = BarcodeFilter(
            request=None,
            params={'barcode': 'barcode_one|barcode_two'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_text_filter_contains(self):
        text_filter = BarcodeFilter(
            request=None,
            params={'barcode': 'one'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_date_filter(self):
        datet_filter = InvoiceDateFilter(
            request=None,
            params={
                'invoice_date_start': '2015-01-20',
                'invoice_date_end': '2015-04-01',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_start(self):
        datet_filter = InvoiceDateFilter(
            request=None,
            params={
                'invoice_date_start': '2015-02-1',
                'invoice_date_end': '',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_end(self):
        datet_filter = InvoiceDateFilter(
            request=None,
            params={
                'invoice_date_start': '',
                'invoice_date_end': '2015-02-20',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())
