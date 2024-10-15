from django.test import SimpleTestCase

from ralph.dashboards.renderers import build_filters


class BuildFilterTestCase(SimpleTestCase):
    def test_without_aggregation(self):
        self.assertEqual(build_filters(labels="id", value=10), {"id": 10})

    def test_with_year_aggregation(self):
        self.assertEqual(
            build_filters(labels="patchdeadline|year", value=2017),
            {
                "patchdeadline__gte": "2017-01-01",
                "patchdeadline__lte": "2017-12-31",
            },
        )

    def test_with_month_aggregation(self):
        self.assertEqual(
            build_filters(labels="patchdeadline|month", value="2017-12"),
            {
                "patchdeadline__gte": "2017-12-01",
                "patchdeadline__lte": "2017-12-31",
            },
        )

    def test_with_day_aggregation(self):
        self.assertEqual(
            build_filters(labels="patchdeadline|day", value="2017-12-01"),
            {
                "patchdeadline__gte": "2017-12-01 00:00:00",
                "patchdeadline__lte": "2017-12-01 23:59:59",
            },
        )
