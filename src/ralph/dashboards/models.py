from dj.choices import Choices
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, Max, Sum
from django_extensions.db.fields.json import JSONField

from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.renderers import HorizontalBar, PieChart, VerticalBar
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


class Dashboard(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin,
    models.Model
):
    active = models.BooleanField(default=True)
    description = models.CharField('description', max_length=250, blank=True)
    graphs = models.ManyToManyField('Graph', blank=True)
    interval = models.PositiveSmallIntegerField(default=60)


class AggregateType(Choices):
    _ = Choices.Choice
    aggregate_count = _('Count').extra(aggregate_func=Count)
    aggregate_max = _('Max').extra(aggregate_func=Max)
    aggregate_sum = _('Sum').extra(aggregate_func=Sum)


class ChartType(Choices):
    # NOTE: append new type
    _ = Choices.Choice
    vertical_bar = _('Verical Bar').extra(renderer=VerticalBar)
    horizontal_bar = _('Horizontal Bar').extra(renderer=HorizontalBar)
    pie_chart = _('Pie Chart').extra(renderer=PieChart)


class Graph(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    description = models.CharField('description', max_length=250, blank=True)
    model = models.ForeignKey(ContentType)
    aggregate_type = models.PositiveIntegerField(choices=AggregateType())
    chart_type = models.PositiveIntegerField(choices=ChartType())
    params = JSONField(blank=True)
    active = models.BooleanField(default=True)

    def pop_annotate_filters(self, filters):
        annotate_filters = {}
        for key in list(filters.keys()):
            if key.startswith('series'):
                annotate_filters.update({key: filters.pop(key)})
        return annotate_filters

    def apply_parital_filtering(self, queryset):
        filters = self.params.get('filters', None)
        excludes = self.params.get('excludes', None)
        if filters:
            queryset = FilterParser(queryset, filters).get_queryset()
        if excludes:
            queryset = FilterParser(
                queryset, excludes, exclude_mode=True
            ).get_queryset()
        return queryset

    def apply_limit(self, queryset):
        limit = self.params.get('limit', None)
        return queryset[:limit]

    def apply_sort(self, queryset):
        order = self.params.get('sort', None)
        if order:
            return queryset.order_by(order)
        return queryset

    def build_queryset(self):
        model = self.model.model_class()
        model_manager = model._default_manager
        aggregate_type = AggregateType.from_id(self.aggregate_type)

        queryset = self.apply_parital_filtering(model_manager.all())

        annotate_filters = {}
        annotate_filters = self.pop_annotate_filters(
            self.params.get('filters', None)
        )

        aggregate_func = aggregate_type.aggregate_func

        queryset = queryset.values(
            self.params['labels']
        ).annotate(
            series=aggregate_func(self.params['series'])
        )

        if annotate_filters:
            queryset = queryset.filter(**annotate_filters)

        queryset = self.apply_sort(queryset)
        queryset = self.apply_limit(queryset)
        return queryset

    def get_data(self):
        queryset = self.build_queryset()
        return {
            'labels': [str(q[self.params['labels']]) for q in queryset],
            'series': [int(q['series']) for q in queryset],
        }

    def render(self, **context):
        chart_type = ChartType.from_id(self.chart_type)
        renderer = getattr(chart_type, 'renderer', None)
        if not renderer:
            raise RuntimeError('Wrong renderer.')
        return renderer(self).render(context)
