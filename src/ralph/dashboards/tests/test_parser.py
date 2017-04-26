import copy
import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.models import AggregateType, Graph
from ralph.dashboards.tests.factories import GraphFactory
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory
)
from ralph.security.tests.factories import (
    SecurityScanFactory,
    VulnerabilityFactory
)
from ralph.tests.models import Bar

ARGS, KWARGS = (0, 1)


@ddt
class ParserFiltersTest(SimpleTestCase):
    def setUp(self):
        self.parser = FilterParser(Bar.objects.all(), None)

    @unpack
    @data(
        ('2y', relativedelta(years=2)),
        ('-2y', relativedelta(years=-2)),
        ('9m', relativedelta(months=9)),
        ('-9m', relativedelta(months=-9)),
        ('55d', relativedelta(days=55)),
        ('-55d', relativedelta(days=-55)),
    )
    def test_filter_from_now(self, filter_str, expect):
        key = 'foo'
        result = self.parser.filter_from_now(key, filter_str)
        pp = datetime.date.today() + expect
        self.assertEqual(
            result[KWARGS], {key: pp.strftime('%Y-%m-%d')}
        )

    @unpack
    @data(
        ('1', Q(key='1')),
        ('1,2', Q(key='1') | Q(key='2')),
    )
    def test_process_value(self, value, expect):
        result = self.parser.filter_or('key', value)
        self.assertEqual(str(result[ARGS][0]), str(expect))

    @unpack
    @data(
        (['1'], Q(key='1')),
        (['1', '2'], Q(key='1') & Q(key='2')),
    )
    def test_process_value_as_list(self, value, expect):
        result = self.parser.filter_and('key', value)
        self.assertEqual(str(result[ARGS][0]), str(expect))

@ddt
class GraphModelTest(SimpleTestCase):
    @unpack
    @data(
        ({}, 0),
        ({'series__lte': 3}, 1),
        ({'series__lte': 5, 'series__qte': 3}, 2),
    )
    def test_annotate_fitler_should_pop_from_filters(
        self, orig_filters, length
    ):
        graph = Graph()
        filters = copy.deepcopy(orig_filters)
        result = graph.pop_annotate_filters(filters)
        self.assertEqual(len(result), length)
        self.assertEqual(len(orig_filters) - length, len(filters))

    def _get_graph_params(self, update):
        data = {
            'filters': {},
            'labels': 'barcode',
            'series': 'price',
        }
        data.update(update)
        return data

    def test_key_limit_limits_records_when_present(self):
        limit = 5
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(
            2 * limit
        )
        graph = GraphFactory(params=self._get_graph_params({'limit': limit}))

        qs = graph.build_queryset()

        self.assertEqual(qs.count(), limit)

    def test_key_sort_sorts_records_ascending_when_present(self):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(10)
        graph = GraphFactory(
            params=self._get_graph_params({'sort': 'barcode'})
        )

        qs = graph.build_queryset()

        self.assertTrue(qs.first()['barcode'] < qs.last()['barcode'])

    def test_key_sort_sorts_records_descending_when_minus_present(self):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(10)
        graph = GraphFactory(
            params=self._get_graph_params({'sort': '-barcode'})
        )

        qs = graph.build_queryset()

        self.assertTrue(qs.first()['barcode'] > qs.last()['barcode'])


class LabelGroupingTest(TestCase):

    def _get_graph_params(self, update):
        data = {
            'filters': {
                'delivery_date__gte': '2016-01-01',
                'delivery_date__lt': '2017-01-01',
            },
            'series': 'id',
        }
        data.update(update)
        return data

    def test_label_works_when_no_grouping_in_label(self):
        self.a_2016 = DataCenterAssetFactory.create_batch(
            2, delivery_date='2015-01-01',
        )
        expected = DataCenterAssetFactory.create_batch(
            1, delivery_date='2016-01-01',
        )
        self.a_2015 = DataCenterAssetFactory.create_batch(
            3, delivery_date='2017-01-01',
        )
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params=self._get_graph_params({
                'labels': 'delivery_date',
            })
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()['series'], len(expected))
        self.assertIn('delivery_date', qs.get())

    def test_label_works_when_year_grouping(self):
        self.a_2016 = DataCenterAssetFactory.create_batch(
            2, delivery_date='2015-01-01',
        )
        expected = DataCenterAssetFactory.create_batch(
            1, delivery_date='2016-01-01',
        )
        self.a_2015 = DataCenterAssetFactory.create_batch(
            3, delivery_date='2017-01-01',
        )
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params=self._get_graph_params({
                'labels': 'delivery_date|year',
            })
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()['series'], len(expected))
        self.assertIn('year', qs.get())

    def _genenrate_dca_with_scan(self, count, date_str):
        gen = []
        for _ in range(count):
            dca = DataCenterAssetFactory()
            sc = SecurityScanFactory(
                last_scan_date=date_str,
            )
            dca.securityscan = sc
            sc.save()
            gen.append(dca)
        return gen

    def test_label_works_when_year_grouping_on_foreign_key(self):
        self._genenrate_dca_with_scan(2, '2015-01-01')
        expected = self._genenrate_dca_with_scan(1, '2016-01-01')
        self._genenrate_dca_with_scan(3, '2017-01-01')

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                'filters': {
                    'securityscan__last_scan_date__gte': '2016-01-01',
                    'securityscan__last_scan_date__lt': '2017-01-01',
                },
                'series': 'id',
                'labels': 'securityscan__last_scan_date|year',
            }
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()['series'], len(expected))
        self.assertIn('year', qs.get())

    def test_xxx(self):
        SecurityScanFactory(
            base_object=DataCenterAssetFactory().baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline='2015-01-01'),
                VulnerabilityFactory(patch_deadline='2015-01-01'),
            ]
        )

        SecurityScanFactory(
            base_object=DataCenterAssetFactory().baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline='2016-01-01'),
                VulnerabilityFactory(patch_deadline='2016-01-01'),
            ]
        )

        SecurityScanFactory(
            base_object=DataCenterAssetFactory().baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(patch_deadline='2017-01-01'),
                VulnerabilityFactory(patch_deadline='2017-01-01'),
            ]
        )

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                'filters': {
                    'securityscan__vulnerabilities__patch_deadline__gte': '2016-01-01',  # noqa
                    'securityscan__vulnerabilities__patch_deadline__lt': '2017-01-01',  # noqa
                },
                'series': 'id',
                'labels': 'securityscan__vulnerabilities__patch_deadline|year',
            }
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()['series'], 1)
        self.assertIn('year', qs.get())
