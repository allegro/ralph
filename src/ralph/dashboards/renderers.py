import json
import logging
from urllib.parse import urlencode

from django.core.urlresolvers import NoReverseMatch, reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


logger = logging.getLogger(__name__)
GRAPH_QUERY_SEP = '|'


class ChartistGraphRenderer(object):
    """Renderer for Chartist.js."""
    func = None
    options = None
    template_name = 'dashboard/templatetags/chartist_render_graph.html'
    _default_options = {
        'distributeSeries': False,
        'chartPadding': 20,
        'height': '350px'
    }
    plugins = {'ctBarLabels': {}}
    graph_query_sep = GRAPH_QUERY_SEP

    def __init__(self, model):
        self.model = model

    def get_func(self):
        if not self.func:
            raise NotImplementedError('Specify func attr.')
        return self.func

    def get_template_name(self):
        if not self.template_name:
            raise NotImplementedError('Specify template_name attr.')
        return self.template_name

    def get_options(self, data=None):
        options = self._default_options.copy()
        if isinstance(self.options, dict):
            options.update(self.options)
        return options

    def _labels2urls(self, model, graph_id, labels):
        meta = model._meta
        base_url = reverse(
            "admin:%s_%s_changelist" % (
                meta.app_label, meta.model_name
            )
        )
        urls = []
        for label in labels:
            url = '?'.join([
                base_url,
                urlencode({
                    'graph-query': self.graph_query_sep.join([
                        str(graph_id), label
                    ])
                }),
            ])
            urls.append(url)

        return urls

    def _series_with_urls(self, series, urls):
        series_with_urls = []
        for value, url in zip(series, urls):
            series_with_urls.append({
                'value': value,
                'meta': {
                    'clickUrl': url,
                }
            })
        return series_with_urls

    def post_data_hook(self, data):
        try:
            click_urls = self._labels2urls(
                self.model.changelist_model, self.model.id, data['labels']
            )
            data['series'] = self._series_with_urls(
                data['series'], click_urls
            )
        except NoReverseMatch as e:
            # graph will be non-clickable when model is not exposed in
            # admin
            logger.error(e)
        return data

    def render(self, context):
        if not context:
            context = {}
        error = None
        data = {}
        try:
            data = self.model.get_data()
            data = self.post_data_hook(data)
        except Exception as e:
            error = str(e)
        finally:
            options = self.get_options(data)
        context.update({
            'error': error,
            'graph': self.model,
            'options': json.dumps(options),
            'options_raw': options,
            'func': self.func,
            'plugins': self.plugins,
        })
        context.update(**data)
        return mark_safe(render_to_string(self.get_template_name(), context))


class HorizontalBar(ChartistGraphRenderer):
    func = 'Bar'
    options = {
        'horizontalBars': True,
        'axisY': {
            'offset': 70,
        },
        'axisX': {
            'onlyInteger': True,
        }
    }


class VerticalBar(ChartistGraphRenderer):
    func = 'Bar'
    options = {
        'axisY': {
            'onlyInteger': True,
        }
    }


class PieChart(ChartistGraphRenderer):
    func = 'Pie'
    _default_options = {
        'distributeSeries': True,
    }
    options = {
        'donut': True,
    }

    def get_options(self, data):
        self.options['total'] = sum(s['value'] for s in data['series'])
        return super().get_options(data)

    def include_values_in_labels(self, data):
        for idx, pack in enumerate(zip(data['labels'], data['series'])):
            label, series = pack
            new_label = "{} ({})".format(label, series['value'])
            data['labels'][idx] = new_label
        return data

    def post_data_hook(self, data):
        super().post_data_hook(data)
        data = self.include_values_in_labels(data)
        return data
