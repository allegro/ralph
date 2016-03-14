import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.test import SimpleTestCase

from ralph.dashboards.filter_parser import FilterParser


@ddt
class ParserFiltersTest(SimpleTestCase):
    def setUp(self):
        self.parser = FilterParser(None, None)

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
        result = self.parser.filter_from_now(filter_str)
        pp = datetime.date.today() + expect
        self.assertEqual(pp.strftime('%Y-%m-%d'), result)
