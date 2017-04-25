from dj.choices import Choices
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
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


class GroupingLabel:
    """
    Adds grouping-by-year feature to query based on `label_group`
    """
    sep = '|'

    def __init__(self, connection, label_group):
        self.connection = connection
        self.orig_label, self.label = self.parse(label_group)

    def parse(self, label_group):
        split = label_group.split(self.sep)
        if len(split) == 1:
            orig_label, label = split[0], split[0]
        elif len(split) == 2:
            orig_label, label = split[0], split[1]
        else:
            raise ValueError("Only one filter supported")
        return orig_label, label

    @property
    def has_filter(self):
        return self.orig_label != self.label

    def filter_year(self):
        field_name = self.orig_label.split('__')[-1]
        return self.connection.ops.date_trunc_sql('year', field_name)

    def apply_filter(self, queryset):
        if self.has_filter:
            queryset = queryset.extra({
                self.label: getattr(self, 'filter_' + self.label)()
            })
        return queryset


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

    @property
    def has_grouping(self):
        labels = self.params.get('labels', '')
        filtering_label = GroupingLabel(connection, labels)
        return filtering_label.has_filter

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

        queryset = model_manager.all()

        filtering_label = GroupingLabel(connection, self.params['labels'])
        queryset = filtering_label.apply_filter(queryset)
        queryset = self.apply_parital_filtering(queryset)

        annotate_filters = self.pop_annotate_filters(
            self.params.get('filters', None)
        )

        aggregate_type = AggregateType.from_id(self.aggregate_type)
        aggregate_func = aggregate_type.aggregate_func
        queryset = queryset.values(
            filtering_label.label
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
        label = GroupingLabel(connection, self.params['labels']).label
        return {
            'labels': [str(q[label]) for q in queryset],
            'series': [int(q['series']) for q in queryset],
        }

    def render(self, **context):
        chart_type = ChartType.from_id(self.chart_type)
        renderer = getattr(chart_type, 'renderer', None)
        if not renderer:
            raise RuntimeError('Wrong renderer.')
        return renderer(self).render(context)
