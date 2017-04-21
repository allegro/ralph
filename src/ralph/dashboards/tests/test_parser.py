import copy
import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.db.models import Q
from django.test import SimpleTestCase

from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.models import Graph
from ralph.dashboards.tests.factories import GraphFactory
from ralph.data_center.tests.factories import DataCenterAssetFullFactory
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
