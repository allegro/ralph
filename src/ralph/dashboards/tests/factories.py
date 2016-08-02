# -*- coding: utf-8 -*-
import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory

from ralph.dashboards.models import AggregateType, ChartType, Dashboard, Graph
from ralph.data_center.models.physical import DataCenterAsset


class DashboardFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'dashboard {}'.format(n))

    class Meta:
        model = Dashboard


class GraphFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'graph {}'.format(n))
    model = ContentType.objects.get_for_model(DataCenterAsset)
    aggregate_type = factory.Iterator([
        AggregateType.aggregate_max.id, AggregateType.aggregate_count.id,
        AggregateType.aggregate_sum.id
    ])
    chart_type = factory.Iterator([
        ChartType.vertical_bar.id, ChartType.horizontal_bar.id,
        ChartType.pie_chart.id
    ])

    class Meta:
        model = Graph
