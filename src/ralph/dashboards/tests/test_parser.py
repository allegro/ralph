import copy
import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from ralph.assets.models import Service
from ralph.assets.tests.factories import ServiceFactory, ServiceEnvironmentFactory
from ralph.dashboards.admin_filters import ByGraphFilter
from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.helpers import encode_params
from ralph.dashboards.models import AggregateType, Graph
from ralph.dashboards.tests.factories import GraphFactory
from ralph.data_center.models import RackOrientation, Rack
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory,
    RackFactory,
)
from ralph.licences.tests.factories import LicenceFactory, DataCenterAssetLicenceFactory
from ralph.tests.models import Bar

ARGS, KWARGS = (0, 1)


@ddt
class ParserFiltersTest(SimpleTestCase):
    def setUp(self):
        self.parser = FilterParser(Bar.objects.all(), None)

    @unpack
    @data(
        ("2y", relativedelta(years=2)),
        ("-2y", relativedelta(years=-2)),
        ("9m", relativedelta(months=9)),
        ("-9m", relativedelta(months=-9)),
        ("55d", relativedelta(days=55)),
        ("-55d", relativedelta(days=-55)),
    )
    def test_filter_from_now(self, filter_str, expect):
        key = "foo"
        result = self.parser.filter_from_now(key, filter_str)
        pp = datetime.date.today() + expect
        self.assertEqual(result[KWARGS], {key: pp.strftime("%Y-%m-%d")})

    @unpack
    @data(
        ("1", Q(key="1")),
        ("1,2", Q(key="1") | Q(key="2")),
    )
    def test_process_value(self, value, expect):
        result = self.parser.filter_or("key", value)
        self.assertEqual(str(result[ARGS][0]), str(expect))

    @unpack
    @data(
        (["1"], Q(key="1")),
        (["1", "2"], Q(key="1") & Q(key="2")),
    )
    def test_process_value_as_list(self, value, expect):
        result = self.parser.filter_and("key", value)
        self.assertEqual(str(result[ARGS][0]), str(expect))


@ddt
class GraphModelTest(TestCase):
    @unpack
    @data(
        ({}, 0),
        ({"series__lte": 3}, 1),
        ({"series__lte": 5, "series__qte": 3}, 2),
    )
    def test_annotate_filter_should_pop_from_filters(self, orig_filters, length):
        graph = Graph()
        filters = copy.deepcopy(orig_filters)
        result = graph.pop_annotate_filters(filters)
        self.assertEqual(len(result), length)
        self.assertEqual(len(orig_filters) - length, len(filters))

    def test_get_data_for_choices_field_returns_names(self):
        test_data = {
            RackOrientation.top.id: 3,
            RackOrientation.bottom.id: 2,
            RackOrientation.left.id: 1,
        }

        rack_orientations = []
        for orientation, count in test_data.items():
            rack_orientations.extend(
                RackFactory.create_batch(count, orientation=orientation)
            )

        graph = GraphFactory(
            model=ContentType.objects.get_for_model(Rack),
            params=self._get_graph_params(
                {
                    "filters": {},
                    "labels": "orientation",
                    "series": "id",
                    "sort": "series",
                }
            ),
        )

        for orientation, count in test_data.items():
            encoded_params = encode_params(
                {
                    "pk": graph.pk,
                    "filters": {"orientation": orientation},
                }
            )
            graph_filter = ByGraphFilter(
                None, {"graph-query": encoded_params}, Rack, None
            )
            qs = graph_filter.queryset(None, Rack.objects.all())

            self.assertEqual(len(qs), count)

        encoded_params = encode_params(
            {"pk": graph.pk, "filters": {"orientation": None}}
        )
        graph_filter = ByGraphFilter(None, {"graph-query": encoded_params}, Rack, None)
        qs = graph_filter.queryset(None, Rack.objects.all())

        self.assertEqual(len(qs), len(Rack.objects.all()) - len(rack_orientations))

    def _get_graph_params(self, update):
        data = {
            "filters": {},
            "labels": "barcode",
            "series": "price",
        }
        data.update(update)
        return data

    def test_key_limit_limits_records_when_present(self):
        limit = 5
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(2 * limit)
        graph = GraphFactory(params=self._get_graph_params({"limit": limit}))

        qs = graph.build_queryset()

        self.assertEqual(qs.count(), limit)

    def test_key_sort_sorts_records_ascending_when_present(self):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(10)
        graph = GraphFactory(params=self._get_graph_params({"sort": "barcode"}))

        qs = graph.build_queryset()

        self.assertTrue(qs.first()["barcode"] < qs.last()["barcode"])

    def test_key_sort_sorts_records_descending_when_minus_present(self):
        self.data_center_assets = DataCenterAssetFullFactory.create_batch(10)
        graph = GraphFactory(params=self._get_graph_params({"sort": "-barcode"}))

        qs = graph.build_queryset()

        self.assertTrue(qs.first()["barcode"] > qs.last()["barcode"])


class LabelGroupingTest(TestCase):
    def _get_graph_params(self, update):
        data = {
            "filters": {
                "delivery_date__gte": "2016-01-01",
                "delivery_date__lt": "2017-01-01",
            },
            "series": "id",
        }
        data.update(update)
        return data

    def test_label_works_when_no_grouping_in_label(self):
        self.a_2016 = DataCenterAssetFactory.create_batch(
            2,
            delivery_date="2015-01-01",
        )
        expected = DataCenterAssetFactory.create_batch(
            1,
            delivery_date="2016-01-01",
        )
        self.a_2015 = DataCenterAssetFactory.create_batch(
            3,
            delivery_date="2017-01-01",
        )
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params=self._get_graph_params(
                {
                    "labels": "delivery_date",
                }
            ),
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("delivery_date", qs.get())

    def test_label_works_when_year_grouping(self):
        self.a_2016 = DataCenterAssetFactory.create_batch(
            2,
            delivery_date="2015-01-01",
        )
        expected = DataCenterAssetFactory.create_batch(
            1,
            delivery_date="2016-01-01",
        )
        self.a_2015 = DataCenterAssetFactory.create_batch(
            3,
            delivery_date="2017-01-01",
        )
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params=self._get_graph_params(
                {
                    "labels": "delivery_date|year",
                }
            ),
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("year", qs.get())

    def _genenrate_dca_with_licence(self, count, date_str):
        gen = []
        for _ in range(count):
            lc = LicenceFactory(valid_thru=date_str)
            dca = DataCenterAssetLicenceFactory(licence=lc)
            gen.append(dca)
        return gen

    def test_label_works_when_year_grouping_on_foreign_key(self):
        self._genenrate_dca_with_licence(2, "2015-01-01")
        expected = self._genenrate_dca_with_licence(1, "2016-01-01")
        self._genenrate_dca_with_licence(3, "2017-01-01")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "licences__licence__valid_thru__gte": "2016-01-01",
                    "licences__licence__valid_thru__lt": "2017-01-01",
                },
                "series": "id",
                "labels": "licences__licence__valid_thru|year",
            },
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("year", qs.get())

    def test_label_works_when_month_grouping_on_foreign_key(self):
        self._genenrate_dca_with_licence(2, "2015-01-01")
        expected = self._genenrate_dca_with_licence(1, "2016-01-01")
        self._genenrate_dca_with_licence(3, "2017-01-01")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "licences__licence__valid_thru__gte": "2016-01-01",
                    "licences__licence__valid_thru__lt": "2017-01-01",
                },
                "series": "id",
                "labels": "licences__licence__valid_thru|month",
            },
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("month", qs.get())

    def test_ratio_aggregation(self):
        service_env = ServiceEnvironmentFactory(service__name="sample-service")
        for is_deprecated in [True, False]:
            for _ in range(3):
                DataCenterAssetFactory(
                    service_env=service_env, force_depreciation=is_deprecated
                )

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_ratio.id,
            params={
                "series": ["force_depreciation", "id"],
                "labels": "service_env__service__name",
                "filters": {
                    "series__gt": 0,
                },
            },
        )

        qs = graph.build_queryset()
        self.assertEqual(
            qs.get(), {"series": 50, "service_env__service__name": "sample-service"}
        )

    def test_duplicates_works_when_used_in_series_value(self):
        DataCenterAssetLicenceFactory(licence=LicenceFactory(valid_thru="2015-01-01"))

        asset = DataCenterAssetFactory()
        for month in [1, 2, 3]:
            licence = LicenceFactory(valid_thru=f"2016-0{month}-01")
            DataCenterAssetLicenceFactory(licence=licence, base_object=asset)

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "licences__licence__valid_thru__gte": "2010-01-01",
                },
                "series": "id|distinct",
                "labels": "licences__licence__valid_thru|year",
            },
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.all()[0]["series"], 1)
        self.assertEqual(qs.all()[1]["series"], 1)

    def test_count_aggregate_with_zeros(self):
        assets_num = 2
        DataCenterAssetFactory.create_batch(assets_num)
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params=self._get_graph_params(
                {
                    "aggregate_expression": "rack__orientation",
                    "filters": {},
                    "labels": "id",
                    "series": "id",
                }
            ),
        )
        qs = graph.build_queryset()
        self.assertEqual(qs.count(), assets_num)
        for item in qs.all():
            self.assertEqual(item["series"], 0)

    def test_count_aggregate_sum_bool_values(self):
        service1 = ServiceFactory(active=True)
        service2 = ServiceFactory(active=False)

        graph = GraphFactory(
            model=ContentType.objects.get_for_model(Service),
            aggregate_type=AggregateType.aggregate_sum_bool_values.id,
            params=self._get_graph_params(
                {
                    "filters": {},
                    "labels": "id",
                    "series": "active",
                }
            ),
        )
        qs = graph.build_queryset()
        self.assertTrue(qs.get(id=service1.id)["series"] == 1)
        self.assertTrue(qs.get(id=service2.id)["series"] == 0)
