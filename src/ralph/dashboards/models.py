from dj.choices import Choices
from dj.choices.fields import ChoiceField
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db.models import Case, Count, IntegerField, Max, Q, Sum, Value, When
from django.db.models.fields import BooleanField
from django.db.models.functions import Coalesce
from django_extensions.db.fields.json import JSONField

from ralph.admin.helpers import get_field_by_relation_path
from ralph.dashboards.filter_parser import FilterParser
from ralph.dashboards.renderers import (
    GRAPH_QUERY_SEP,
    HorizontalBar,
    PieChart,
    VerticalBar
)
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


def _unpack_series(series):
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


def ratio_handler(aggregate_func, series, aggregate_expression):
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
        )) * 100.0 / Count(series[1])
    )


def zero_handler(aggregate_func, series, aggregate_expression):
    series_field, _ = _unpack_series(series)
    return (
        Coalesce(
            Count(aggregate_expression or series_field), Value(0),
            output_field=IntegerField())
    )


def sum_bool_value_handler(aggregate_func, series, aggregate_expression):
    series_field, _ = _unpack_series(series)
    aggregate_expression = aggregate_expression or series_field
    return Sum(
        Case(
            When(Q(**{aggregate_expression: True}), then=Value(1)),
            When(Q(**{aggregate_expression: False}), then=Value(0)),
            default=Value(0),
            output_field=IntegerField()
        )
    )


class AggregateType(Choices):
    _ = Choices.Choice
    aggregate_count = _('Count').extra(aggregate_func=Count)
    aggregate_count_with_zeros = _('Count with zeros').extra(
        aggregate_func=Count, handler=zero_handler
    )
    aggregate_max = _('Max').extra(aggregate_func=Max)
    aggregate_sum = _('Sum').extra(aggregate_func=Sum)
    aggregate_sum_bool_values = _('Sum boolean values').extra(
        aggregate_func=Sum, handler=sum_bool_value_handler
    )
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
    date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
    date_format = ('%Y-', '%m', '-%d', ' %H:', '%i', ':%s')

    def __init__(self, connection, label_group):
        self.connection = connection
        self.orig_label, self.label = self.parse(label_group)

    def parse(self, label_group):
        return _to_pair(label_group, self.sep)

    @property
    def has_group(self):
        return self.orig_label != self.label

    def _group_by_part_of_date(self, date_part):
        field_name = self.orig_label.split('__')[-1]
        return self.connection.ops.date_trunc_sql(date_part, field_name)

    def apply_grouping(self, queryset):
        if self.has_group:
            if self.label in self.date_fields:
                queryset = queryset.extra({
                    self.label: self._group_by_part_of_date(self.label)
                })
            else:
                queryset = queryset.extra({
                    self.label: getattr(self, 'group_' + self.label)()
                })
        return queryset

    def _format_part_of_date(self, value):
        i = self.date_fields.index(self.label) + 1
        format_str = ''.join([f for f in self.date_format[:i]])
        return value.strftime(format_str)

    def format_label(self, value):
        if self.has_group:
            value = self._format_part_of_date(value).strip('-').strip(':')
        return str(value)


class Graph(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    description = models.CharField('description', max_length=250, blank=True)
    model = models.ForeignKey(ContentType)
    aggregate_type = models.PositiveIntegerField(choices=AggregateType())
    chart_type = models.PositiveIntegerField(choices=ChartType())
    params = JSONField(blank=True)
    active = models.BooleanField(default=True)
    push_to_statsd = models.BooleanField(
        default=False,
        help_text='Push graph\'s data to statsd.'
    )

    @property
    def changelist_model(self):
        return (self.custom_changelist_model or self.model).model_class()

    @property
    def custom_changelist_model(self):
        model_name_from_params = (
            self.params.get('target') and self.params['target'].get('model')
        )
        if not model_name_from_params:
            return None
        try:
            return ContentType.objects.get(
                model=model_name_from_params.lower()
            )
        except ContentType.DoesNotExist:
            raise ValueError(
                'Model "{}" does not exist.'
                'Please provide correct model to target.model'.format(
                    model_name_from_params
                )
            )

    @property
    def custom_changelist_filter_key(self):
        return (
            self.params.get('target') and self.params['target'].get('filter')
        )

    @property
    def changelist_filter_key(self):
        return self.custom_changelist_filter_key or self.params['labels']

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

    def get_aggregation(self):
        aggregate_type = AggregateType.from_id(self.aggregate_type)
        aggregate_func = aggregate_type.aggregate_func
        # aggregate choice might have defined custom handler
        handler = getattr(
            aggregate_type, 'handler', self._default_aggregation_handler
        )
        series = self.params.get('series', '')
        aggregate_expression = self.params.get('aggregate_expression')
        return handler(
            aggregate_func=aggregate_func,
            series=series,
            aggregate_expression=aggregate_expression,
        )

    def _default_aggregation_handler(
        self, aggregate_func, series, aggregate_expression
    ):
        series_field, fn_name = _unpack_series(series)
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
        return aggregate_func(
            aggregate_expression or series_field,
            **aggregate_fn_kwargs
        )

    def build_queryset(self, annotated=True, queryset=None):
        model = self.model.model_class()
        model_manager = model._default_manager
        queryset = queryset or model_manager.all()

        grouping_label = GroupingLabel(connection, self.params['labels'])
        if annotated:
            queryset = grouping_label.apply_grouping(queryset)
        # pop filters which are applied on annotated queryset
        annotate_filters = self.pop_annotate_filters(
            self.params.get('filters', {})
        )
        queryset = self.apply_parital_filtering(queryset)
        if annotated:
            queryset = queryset.values(
                grouping_label.label
            ).annotate(
                series=self.get_aggregation(),
            )
        if annotate_filters:
            queryset = queryset.filter(**annotate_filters)
        if annotated:
            queryset = self.apply_sort(queryset)
            queryset = self.apply_limit(queryset)
        return queryset

    def get_data(self):
        queryset = self.build_queryset()
        grouping_label = GroupingLabel(connection, self.params['labels'])
        label = grouping_label.label
        return {
            'labels': [
                grouping_label.format_label(q[label]) for q in queryset
            ],
            'series': [int(q['series']) for q in queryset],
        }

    def render(self, **context):
        chart_type = ChartType.from_id(self.chart_type)
        renderer = getattr(chart_type, 'renderer', None)
        if not renderer:
            raise RuntimeError('Wrong renderer.')
        return renderer(self).render(context)

    def normalize_changelist_value(self, graph_item):
        field = get_field_by_relation_path(
            self.model.model_class(),
            self.params['labels'].split(GRAPH_QUERY_SEP)[0]
        )
        if isinstance(field, ChoiceField):
            choices = field.choice_class()
            try:
                graph_item = [
                    i[0] for i in choices if i[1] == graph_item
                ].pop()
            except IndexError:
                # NOTE(romcheg): Choice not found for the filter value.
                #                Leaving it as is.
                pass
        elif isinstance(field, BooleanField):
            graph_item = field.to_python(graph_item)
        return graph_item

    def get_queryset_for_filter(self, queryset, value):
        filter_key = self.changelist_filter_key
        value = self.normalize_changelist_value(value)
        if self.custom_changelist_model:
            value_param = self.params['target'].get('value', 'id')
            values = self.build_queryset(annotated=False).filter(
                **{self.params['labels']: value}
            ).values_list(value_param, flat=True)
            queryset = queryset.filter(**{filter_key: values})
        else:
            queryset = self.build_queryset(annotated=False, queryset=queryset)
            queryset = queryset.filter(
                **{self.params['labels'].replace(GRAPH_QUERY_SEP, '__'): value}
            )
        return queryset
