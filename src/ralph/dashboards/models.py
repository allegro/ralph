from dj.choices import Choices
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db.models import Case, Count, IntegerField, Max, Q, Sum, Value, When
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


def ratio_handler(queryset, series):
    if not isinstance(series, list):
        raise ValueError('Ratio aggregation requires series to be list')
    if len(series) != 2:
        raise ValueError(
            'Ratio aggregation requires series to be list of size 2'
        )
    # postgres does not support Sum with boolean field so we need to use
    # Case-When with integer values here
    return (
        Sum(Case(
            When(Q(**{series[0]: True}), then=Value(1)),
            When(Q(**{series[0]: False}), then=Value(0)),
            default=Value(0),
            output_field=IntegerField()
        )) / Count(series[1]) * 100.0
    )


class AggregateType(Choices):
    _ = Choices.Choice
    aggregate_count = _('Count').extra(aggregate_func=Count)
    aggregate_max = _('Max').extra(aggregate_func=Max)
    aggregate_sum = _('Sum').extra(aggregate_func=Sum)
    aggregate_ratio = _('Ratio').extra(
        aggregate_func=Count, handler=ratio_handler
    )


class ChartType(Choices):
    # NOTE: append new type
    _ = Choices.Choice
    vertical_bar = _('Verical Bar').extra(renderer=VerticalBar)
    horizontal_bar = _('Horizontal Bar').extra(renderer=HorizontalBar)
    pie_chart = _('Pie Chart').extra(renderer=PieChart)


def _to_pair(text, sep):
    split = text.split(sep)
    if len(split) == 1:
        orig_label, label = split[0], split[0]
    elif len(split) == 2:
        orig_label, label = split[0], split[1]
    else:
        raise ValueError("Only one group supported")
    return orig_label, label


class GroupingLabel:
    """
    Adds grouping-by-year feature to query based on `label_group`
    """
    sep = '|'

    def __init__(self, connection, label_group):
        self.connection = connection
        self.orig_label, self.label = self.parse(label_group)

    def parse(self, label_group):
        return _to_pair(label_group, self.sep)

    @property
    def has_group(self):
        return self.orig_label != self.label

    def group_year(self):
        field_name = self.orig_label.split('__')[-1]
        return self.connection.ops.date_trunc_sql('year', field_name)

    def apply_grouping(self, queryset):
        if self.has_group:
            queryset = queryset.extra({
                self.label: getattr(self, 'group_' + self.label)()
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
        grouping_label = GroupingLabel(connection, labels)
        return grouping_label.has_group

    def apply_limit(self, queryset):
        limit = self.params.get('limit', None)
        return queryset[:limit]

    def apply_sort(self, queryset):
        order = self.params.get('sort', None)
        if order:
            return queryset.order_by(order)
        return queryset

    def _unpack_series(self, series):
        if not isinstance(series, str):
            raise ValueError('Series should be string')
        series_field, fn = _to_pair(series, '|')
        if (series_field != fn) and (fn != 'distinct'):
            raise ValueError(
                "Series supports Only `distinct` (you put '{}')".format(fn)  # noqa
            )
        if not series_field:
            raise ValueError("Field `series` can't be empty")
        return series_field, fn

    def get_aggregation(self):
        aggregate_type = AggregateType.from_id(self.aggregate_type)
        aggregate_func = aggregate_type.aggregate_func
        # aggregate choice might have defined custom handler
        handler = getattr(
            aggregate_type, 'handler', self._default_aggregation_handler
        )
        return handler(aggregate_func, self.params.get('series', ''))

    def _default_aggregation_handler(self, aggregate_func, series):
        series_field, fn_name = self._unpack_series(series)
        aggregate_fn_kwargs = {}
        if fn_name == "distinct":
            if self.aggregate_type != AggregateType.aggregate_count.id:
                raise ValueError(
                    "{} can by only used with {}".format(
                        AggregateType.from_id(self.aggregate_type).desc,
                        fn_name,
                    )
                )

            aggregate_fn_kwargs['distinct'] = True
        return aggregate_func(series_field, **aggregate_fn_kwargs)

    def build_queryset(self):
        model = self.model.model_class()
        model_manager = model._default_manager
        queryset = model_manager.all()

        grouping_label = GroupingLabel(connection, self.params['labels'])
        queryset = grouping_label.apply_grouping(queryset)
        # pop filters which are applied on annotated queryset
        annotate_filters = self.pop_annotate_filters(
            self.params.get('filters', {})
        )
        queryset = self.apply_parital_filtering(queryset)
        queryset = queryset.values(
            grouping_label.label
        ).annotate(
            series=self.get_aggregation(),
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
