import copy
import datetime

from dateutil.relativedelta import relativedelta
from ddt import data, ddt, unpack
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.configuration_management.models import SCMCheckResult
from ralph.configuration_management.tests.factories import SCMStatusCheckFactory
from ralph.dashboards.admin_filters import ByGraphFilter
from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.helpers import encode_params
from ralph.dashboards.models import AggregateType, Graph
from ralph.dashboards.tests.factories import GraphFactory
from ralph.data_center.admin import DataCenterAdmin
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    DataCenterAssetFullFactory
)
from ralph.security.models import Vulnerability
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
    def test_annotate_fitler_should_pop_from_filters(self, orig_filters, length):
        graph = Graph()
        filters = copy.deepcopy(orig_filters)
        result = graph.pop_annotate_filters(filters)
        self.assertEqual(len(result), length)
        self.assertEqual(len(orig_filters) - length, len(filters))

    def test_get_data_for_choices_field_returns_names(self):
        test_data = {
            SCMCheckResult.scm_ok: 3,
            SCMCheckResult.check_failed: 2,
            SCMCheckResult.scm_error: 1,
        }

        data_center_assets = DataCenterAssetFullFactory.create_batch(
            10, scmstatuscheck=None
        )
        scm_checks = []

        dca_number = 0
        for check_result in test_data:
            for i in range(test_data[check_result]):
                scm_checks.append(
                    SCMStatusCheckFactory(
                        check_result=check_result,
                        base_object=data_center_assets[dca_number],
                    )
                )
                dca_number += 1

        graph = GraphFactory(
            params=self._get_graph_params(
                {
                    "filters": {},
                    "labels": "scmstatuscheck__check_result",
                    "series": "id",
                    "sort": "series",
                }
            )
        )

        for check_result in test_data:
            encoded_params = encode_params(
                {
                    "pk": graph.pk,
                    "filters": {"scmstatuscheck__check_result": check_result.id},
                }
            )
            graph_filter = ByGraphFilter(
                None, {"graph-query": encoded_params}, DataCenterAsset, DataCenterAdmin
            )
            qs = graph_filter.queryset(None, DataCenterAsset.objects.all())

            self.assertEqual(len(qs), test_data[check_result])

        encoded_params = encode_params(
            {"pk": graph.pk, "filters": {"scmstatuscheck__check_result": None}}
        )
        graph_filter = ByGraphFilter(
            None, {"graph-query": encoded_params}, DataCenterAsset, DataCenterAdmin
        )
        qs = graph_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(len(qs), len(data_center_assets) - dca_number)

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
        self._genenrate_dca_with_scan(2, "2015-01-01")
        expected = self._genenrate_dca_with_scan(1, "2016-01-01")
        self._genenrate_dca_with_scan(3, "2017-01-01")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "securityscan__last_scan_date__gte": "2016-01-01",
                    "securityscan__last_scan_date__lt": "2017-01-01",
                },
                "series": "id",
                "labels": "securityscan__last_scan_date|year",
            },
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("year", qs.get())

    def test_label_works_when_month_grouping_on_foreign_key(self):
        self._genenrate_dca_with_scan(2, "2015-01-01")
        expected = self._genenrate_dca_with_scan(1, "2016-01-01")
        self._genenrate_dca_with_scan(3, "2017-01-01")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "securityscan__last_scan_date__gte": "2016-01-01",
                    "securityscan__last_scan_date__lt": "2017-01-01",
                },
                "series": "id",
                "labels": "securityscan__last_scan_date|month",
            },
        )

        qs = graph.build_queryset()

        self.assertEqual(qs.get()["series"], len(expected))
        self.assertIn("month", qs.get())

    def test_ratio_aggregation(self):
        service_env = ServiceEnvironmentFactory(service__name="sample-service")
        vulnerability = VulnerabilityFactory(patch_deadline=datetime.date(2015, 1, 1))
        for is_patched in [True, False]:
            for _ in range(3):
                dca = DataCenterAssetFactory(service_env=service_env)
                if is_patched:
                    ss = SecurityScanFactory(vulnerabilities=[])
                else:
                    ss = SecurityScanFactory(vulnerabilities=[vulnerability])
                dca.securityscan = ss
                ss.save()
                dca.save()
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_ratio.id,
            params={
                "series": ["securityscan__is_patched", "id"],
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
        SecurityScanFactory(
            base_object=DataCenterAssetFactory().baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(
                    patch_deadline=datetime.datetime.strptime("2015-01-01", "%Y-%m-%d")
                ),
            ],
        )

        SecurityScanFactory(
            base_object=DataCenterAssetFactory().baseobject_ptr,
            vulnerabilities=[
                VulnerabilityFactory(
                    patch_deadline=datetime.datetime.strptime("2016-01-01", "%Y-%m-%d")
                ),
                VulnerabilityFactory(
                    patch_deadline=datetime.datetime.strptime("2016-02-02", "%Y-%m-%d")
                ),
                VulnerabilityFactory(
                    patch_deadline=datetime.datetime.strptime("2016-03-03", "%Y-%m-%d")
                ),
            ],
        )

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "filters": {
                    "patch_deadline__gte": "2010-01-01",
                    "securityscan__base_object__isnull": False,
                },
                "series": "securityscan|distinct",
                "labels": "patch_deadline|year",
            },
        )
        graph.model = ContentType.objects.get_for_model(Vulnerability)
        graph.save()

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
                    "aggregate_expression": "scmstatuscheck",
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
        assets_num = 2
        a, b = DataCenterAssetFactory.create_batch(assets_num)
        SCMStatusCheckFactory(base_object=a, check_result=SCMCheckResult.scm_ok.id)
        SCMStatusCheckFactory(base_object=b, check_result=SCMCheckResult.scm_error.id)
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_sum_bool_values.id,
            params=self._get_graph_params(
                {
                    "filters": {},
                    "labels": "id",
                    "series": "scmstatuscheck__ok",
                }
            ),
        )
        qs = graph.build_queryset()
        self.assertTrue(qs.get(id=a.id)["series"] == 1)
        self.assertTrue(qs.get(id=b.id)["series"] == 0)
