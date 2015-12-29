# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from ralph.admin.filters import (
    BooleanListFilter,
    ChoicesListFilter,
    date_format_to_human,
    DateListFilter,
    LiquidatedStatusFilter,
    NumberListFilter,
    RelatedFieldListFilter,
    TagsListFilter,
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
from ralph.supports.admin import SupportAdmin
from ralph.supports.models import Support
from ralph.supports.tests.factories import SupportFactory


class AdminFiltersTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dca_1 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 1, 1),
            barcode='barcode_one',
            status=DataCenterAssetStatus.new,
        )
        cls.dca_1.tags.add('tag_1')
        cls.dca_2 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 2, 1),
            barcode='barcode_two',
            status=DataCenterAssetStatus.liquidated,
        )
        cls.dca_2.tags.add('tag_1')
        cls.dca_3 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 3, 1),
            force_depreciation=True,
            status=DataCenterAssetStatus.used,
        )
        cls.dca_3.tags.add('tag_2')
        cls.dca_4 = DataCenterAssetFactory(
            rack=RackFactory()
        )
        cls.support_1 = SupportFactory(price=10)
        cls.support_2 = SupportFactory(price=100)

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

        self.assertEqual(2, queryset.count())

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

    def test_text_filter_with_separator_and_whitespace(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field('barcode'),
            request=None,
            params={'barcode': ' barcode_one | barcode_two'},
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
            field=DataCenterAsset._meta.get_field('rack'),
            request=None,
            params={
                'rack': self.dca_4.rack.id,
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='rack'
        )
        queryset = related_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())

    def test_decimal_filter(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field('price'),
            request=None,
            params={
                'price__start': 0,
                'price__end': 200,
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path='price'
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(2, queryset.count())

    def test_decimal_filter_start(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field('price'),
            request=None,
            params={
                'price__start': 50,
                'price__end': '',
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path='price'
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(1, queryset.count())

    def test_decimal_filter_end(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field('price'),
            request=None,
            params={
                'price__start': '',
                'price__end': 50,
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path='price'
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(1, queryset.count())

    def test_liquidated_status_filter(self):
        liquidated_filter = LiquidatedStatusFilter(
            request=None,
            params={'liquidated': '1',},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = liquidated_filter.queryset(
            None, DataCenterAsset.objects.all()
        )
        self.assertEqual(4, queryset.count())

        liquidated_filter = LiquidatedStatusFilter(
            request=None,
            params={'liquidated': None,},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = liquidated_filter.queryset(
            None, DataCenterAsset.objects.all()
        )
        self.assertEqual(3, queryset.count())

    def test_tags_filter(self):
        tags_filter = TagsListFilter(
            field=Support._meta.get_field('tags'),
            request=None,
            params={'tags': 'tag_1'},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path='tags',
        )
        queryset = tags_filter.queryset(None, DataCenterAsset.objects.all())
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.dca_1, queryset)
        self.assertIn(self.dca_2, queryset)
