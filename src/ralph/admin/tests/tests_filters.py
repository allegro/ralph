# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from ralph.admin.filters import (
    BooleanListFilter,
    ChoicesListFilter,
    date_format_to_human,
    DateListFilter,
    RelatedFieldListFilter,
    TextListFilter
)
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.models.physical import (
    DataCenterAsset,
    DataCenterAssetStatus,
    Rack
)
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)


class AdminFiltersTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dca_1 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 1, 1),
            barcode='barcode_one',
            status=DataCenterAssetStatus.new,
        )
        cls.dca_2 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 2, 1),
            barcode='barcode_two',
            status=DataCenterAssetStatus.new,
        )
        cls.dca_3 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 3, 1),
            force_depreciation=True,
            status=DataCenterAssetStatus.used,
        )
        cls.dca_4 = DataCenterAssetFactory(
            rack=RackFactory()
        )

    def test_date_format_to_human(self):
        self.assertEqual('YYYY-MM-DD', date_format_to_human('%Y-%m-%d'))
        self.assertEqual('YY-DD-MM', date_format_to_human('%y-%d-%m'))

    def test_boolean_filter(self):
        boolean_filter = BooleanListFilter(
            field=DataCenterAsset._meta.get_field('force_depreciation'),
            request=None,
            params={'force_depreciation': True},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='force_depreciation'
        )
        queryset = boolean_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_3.pk, queryset.first().pk)

    def test_choices_filter(self):
        choices_filter = ChoicesListFilter(
            field=DataCenterAsset._meta.get_field('status'),
            request=None,
            params={'status': DataCenterAssetStatus.new},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='status'
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(3, queryset.count())

        choices_filter = ChoicesListFilter(
            field=DataCenterAsset._meta.get_field('status'),
            request=None,
            params={'status': DataCenterAssetStatus.used},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='status'
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())

    def test_text_filter(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field('barcode'),
            request=None,
            params={'barcode': 'barcode_one'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='barcode'
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_text_filter_with_separator(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field('barcode'),
            request=None,
            params={'barcode': 'barcode_one|barcode_two'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='barcode'
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_text_filter_contains(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field('barcode'),
            request=None,
            params={'barcode': 'one'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='barcode'
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_date_filter(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field('invoice_date'),
            request=None,
            params={
                'invoice_date__start': '2015-01-20',
                'invoice_date__end': '2015-04-01',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='invoice_date'
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_start(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field('invoice_date'),
            request=None,
            params={
                'invoice_date__start': '2015-02-1',
                'invoice_date__end': '',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='invoice_date'
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_end(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field('invoice_date'),
            request=None,
            params={
                'invoice_date__start': '',
                'invoice_date__end': '2015-02-20',
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='invoice_date'
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_related_field(self):
        related_filter = RelatedFieldListFilter(
            field=Rack._meta.get_field('name'),
            request=None,
            params={
                'rack__name': self.dca_4.rack.name,
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='rack__name'
        )
        queryset = related_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())
