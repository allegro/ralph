from django.urls import reverse

from ralph.api.tests._base import RalphAPITestCase
from ralph.dashboards.models import AggregateType
from ralph.dashboards.tests.factories import GraphFactory


class GraphAPITestCase(RalphAPITestCase):
    def test_endpoint_should_return_get_data_and_params(self):
        graph = GraphFactory(
            aggregate_type=AggregateType.aggregate_count.id,
            params={
                "series": "id",
                "labels": "hostname",
            },
        )
        url = reverse("graph-detail", args=(graph.id,))
        response = self.client.get(url)
        self.assertEqual(
            response.data,
            {
                "name": graph.name,
                "description": graph.description,
                "data": graph.get_data(),
                "params": graph.params,
            },
        )
