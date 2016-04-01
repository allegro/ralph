import copy
import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.db.models import Q
from django.test import SimpleTestCase

from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.models import Graph
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
    def test_process_value(self, value, expect):
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
