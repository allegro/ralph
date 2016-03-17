import json

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class ChartistGraphRenderer(object):
    """Renderer for Chartist.js."""
    func = None
    options = None
    template_name = 'dashboard/templatetags/chartist_render_graph.html'
    _default_options = {
        'distributeSeries': False,
        'chartPadding': 20,
    }
    plugins = {'ctBarLabels': {}}

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

    def render(self, context):
        if not context:
            context = {}
        data = self.model.get_data()
        options = self.get_options(data)
        context.update({
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
        self.options['total'] = sum(data['series'])
        return super().get_options(data)
