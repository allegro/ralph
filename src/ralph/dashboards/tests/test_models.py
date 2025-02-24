from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.assets.models import ServiceEnvironment
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.configuration_management.models import SCMCheckResult
from ralph.dashboards.models import AggregateType
from ralph.dashboards.tests.factories import GraphFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFullFactory


class GraphQuerysetForFilterTestCase(TestCase):
    def test_filtering_queryset(self):
        DataCenterAssetFullFactory.create_batch(
            2,
            service_env__service__name="ServiceA",
        )
        DataCenterAssetFullFactory.create_batch(
            1,
            service_env__service__name="ServiceB",
        )
        DataCenterAssetFullFactory.create_batch(
            3,
            service_env__service__name="ServiceC",
        )
        ServiceEnvironmentFactory.create(service__name="ServiceD")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "series": "id",
                "labels": "service_env__service__name",
            },
        )

        dca_qs = DataCenterAsset.objects.all()
        filtered_qs = graph.get_queryset_for_filter(
            dca_qs,
            {
                "service_env__service__name": "ServiceA",
            },
        )

        self.assertEqual(filtered_qs.count(), 2)
        self.assertEqual(
            list(filtered_qs.values_list("service_env__service__name", flat=True)),
            ["ServiceA", "ServiceA"],
        )

    def test_filtering_queryset_with_target_model(self):
        DataCenterAssetFullFactory.create_batch(
            2,
            service_env__service__name="ServiceA",
        )
        DataCenterAssetFullFactory.create_batch(
            1,
            service_env__service__name="ServiceB",
        )
        DataCenterAssetFullFactory.create_batch(
            3,
            service_env__service__name="ServiceC",
        )
        ServiceEnvironmentFactory.create(service__name="ServiceD")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "series": "id",
                "labels": "service__name",
                "target": {
                    "model": "DataCenterAsset",
                    "filter": "service_env__service__name__in",
                    "value": "service__name",
                },
            },
        )
        graph.model = ContentType.objects.get_for_model(ServiceEnvironment)
        graph.save()

        dca_qs = DataCenterAsset.objects.all()
        filtered_qs = graph.get_queryset_for_filter(
            dca_qs,
            {
                "service__name": "ServiceA",
            },
        )
        self.assertEqual(filtered_qs.count(), 2)
        self.assertEqual(
            list(filtered_qs.values_list("service_env__service__name", flat=True)),
            ["ServiceA", "ServiceA"],
        )

    def test_filtering_queryset_with_additional_filters(self):
        service_env_a = ServiceEnvironmentFactory(service__name="ServiceA")
        DataCenterAssetFullFactory.create_batch(
            2, service_env=service_env_a, scmstatuscheck=None
        )
        DataCenterAssetFullFactory.create_batch(
            3,
            service_env=service_env_a,
            scmstatuscheck__check_result=SCMCheckResult.scm_error,
        )
        DataCenterAssetFullFactory.create_batch(
            4, service_env=service_env_a, scmstatuscheck__ok=True
        )
        DataCenterAssetFullFactory.create_batch(
            1,
            service_env__service__name="ServiceB",
        )
        DataCenterAssetFullFactory.create_batch(
            3,
            service_env__service__name="ServiceC",
        )
        ServiceEnvironmentFactory.create(service__name="ServiceD")

        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_sum_bool_negated_values.id,
            params={
                "series": "id",
                "labels": "service__name",
                "target": {
                    "model": "DataCenterAsset",
                    "filter": "service_env__service__name__in",
                    "value": "service__name",
                    "additional_filters": {"scmstatuscheck__ok": False},
                },
            },
            model=ContentType.objects.get_for_model(ServiceEnvironment),
        )

        dca_qs = DataCenterAsset.objects.all()
        filtered_qs = graph.get_queryset_for_filter(
            dca_qs, {"service__name": "ServiceA"}
        )
        self.assertEqual(filtered_qs.count(), 3)
        self.assertEqual(
            list(
                filtered_qs.values_list(
                    "service_env__service__name", "scmstatuscheck__ok"
                )
            ),
            [("ServiceA", False)] * 3,
        )
