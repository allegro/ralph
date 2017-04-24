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


class FilteringLabels():
    #TODO:: docs
    sep = '|'

    def __init__(self, connection, label_filter):
        self.connection = connection
        self.label_filter = label_filter
        self.label, self.filters = self.parse(label_filter)

    def parse(self, extra):
        split = self.label_filter.split(self.sep)
        if len(split) > 1:
            label, *filters = split[0]
        else:
            label, filters = split[0], []

        return label, filters

    def filter_year(self, extra):
        return self.connection.ops.date_trunc_sql('year', self.label)

    def apply_filters(self, queryset):
        extra = {}
        for filter_name in self.filters:
            filter_fn = getattr(self, 'filter_' + filter_name)()
            extra[filter_name] = filter_fn
        with_filters = queryset.extra(extra)
        return with_filters


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

        queryset = model_manager.all()


        filtering_label = FilteringLabels(connection, self.params['labels'])
        queryset = filtering_label.apply_filters(queryset)
        print(queryset.query)
        #from django.db import connection
        #from django.db.models import Sum, Count
        #from ralph.data_center.models import DataCenterAsset
        #truncate_date = connection.ops.date_trunc_sql('year', 'securityscan__vulnerabilities__patch_deadline')
        ##qs = DataCenterAsset.objects
        #qs = DataCenterAsset.objects.extra({'year': truncate_date})

        #res = qs.filter(
        #    securityscan__vulnerabilities__patch_deadline__gte='2016-01-01',
        #    securityscan__vulnerabilities__patch_deadline__lte='2017-01-01'
        #).distinct().annotate(
        #    Count('id')
        #).values_list(
        #    'securityscan__vulnerabilities__patch_deadline', flat=True
        #).all()
        #import ipdb
        #ipdb.set_trace()






        queryset = self.apply_parital_filtering(queryset)

        annotate_filters = self.pop_annotate_filters(
            self.params.get('filters', None)
        )

        aggregate_type = AggregateType.from_id(self.aggregate_type)
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



        print(queryset.query)
        print(queryset.all())
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
