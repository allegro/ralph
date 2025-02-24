import calendar
import json
import logging
from urllib.parse import urlencode

from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from ralph.dashboards.helpers import encode_params, normalize_value

logger = logging.getLogger(__name__)
GRAPH_QUERY_SEP = "|"


def build_filters(labels, value):
    params = labels.split(GRAPH_QUERY_SEP)
    if len(params) == 1:
        return {params[0]: value}
    if len(params) == 2:
        field, aggr = params
        if aggr == "year":
            return {
                "{}__gte".format(field): "{}-01-01".format(value),
                "{}__lte".format(field): "{}-12-31".format(value),
            }
        if aggr == "month":
            year, month = value.split("-")
            days_in_month = calendar.monthrange(int(year), int(month))[1]
            return {
                "{}__gte".format(field): "{}-01".format(value),
                "{}__lte".format(field): "{}-{}".format(value, days_in_month),
            }
        if aggr == "day":
            return {
                "{}__gte".format(field): "{} 00:00:00".format(value),
                "{}__lte".format(field): "{} 23:59:59".format(value),
            }
    return {}


class ChartistGraphRenderer(object):
    """Renderer for Chartist.js."""

    func = None
    options = None
    template_name = "dashboard/templatetags/chartist_render_graph.html"
    _default_options = {
        "distributeSeries": False,
        "chartPadding": 20,
        "height": "350px",
    }
    plugins = {"ctBarLabels": {}}
    graph_query_sep = GRAPH_QUERY_SEP

    def __init__(self, obj):
        self.obj = obj

    def get_func(self):
        if not self.func:
            raise NotImplementedError("Specify func attr.")
        return self.func

    def get_template_name(self):
        if not self.template_name:
            raise NotImplementedError("Specify template_name attr.")
        return self.template_name

    def get_options(self, data=None):
        options = self._default_options.copy()
        if isinstance(self.options, dict):
            options.update(self.options)
        return options

    def _labels2urls(self, model, graph_id, values):
        meta = model._meta
        base_url = reverse("admin:%s_%s_changelist" % (meta.app_label, meta.model_name))
        urls = []
        for value in values:
            labels = self.obj.params["labels"]
            url = "?".join(
                [
                    base_url,
                    urlencode(
                        {
                            "graph-query": encode_params(
                                {
                                    "pk": graph_id,
                                    "filters": build_filters(
                                        labels=labels,
                                        value=normalize_value(
                                            label=labels.split(GRAPH_QUERY_SEP)[0],
                                            model_class=self.obj.model.model_class(),
                                            value=value,
                                        ),
                                    ),
                                }
                            )
                        }
                    ),
                ]
            )
            urls.append(url)

        return urls

    def _series_with_urls(self, series, urls):
        series_with_urls = []
        for value, url in zip(series, urls):
            series_with_urls.append(
                {
                    "value": value,
                    "meta": {
                        "clickUrl": url,
                    },
                }
            )
        return series_with_urls

    def post_data_hook(self, data):
        try:
            click_urls = self._labels2urls(
                self.obj.changelist_model, self.obj.id, data["labels"]
            )
            data["series"] = self._series_with_urls(data["series"], click_urls)
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
            data = self.obj.get_data()
            data = self.post_data_hook(data)
        except Exception as e:
            error = str(e)
        finally:
            options = self.get_options(data)
        context.update(
            {
                "error": error,
                "graph": self.obj,
                "options": json.dumps(options),
                "options_raw": options,
                "func": self.func,
                "plugins": self.plugins,
            }
        )
        context.update(**data)
        return mark_safe(render_to_string(self.get_template_name(), context))


class HorizontalBar(ChartistGraphRenderer):
    func = "Bar"
    options = {
        "horizontalBars": True,
        "axisY": {
            "offset": 70,
        },
        "axisX": {
            "onlyInteger": True,
        },
    }


class VerticalBar(ChartistGraphRenderer):
    func = "Bar"
    options = {
        "axisY": {
            "onlyInteger": True,
        }
    }


class PieChart(ChartistGraphRenderer):
    func = "Pie"
    _default_options = {
        "distributeSeries": True,
    }
    options = {
        "donut": True,
    }

    def get_options(self, data):
        series = data.get("series")
        if series:
            self.options["total"] = sum(s["value"] for s in series)
        return super().get_options(data)

    def include_values_in_labels(self, data):
        for idx, pack in enumerate(zip(data["labels"], data["series"])):
            label, series = pack
            new_label = "{} ({})".format(label, series["value"])
            data["labels"][idx] = new_label
        return data

    def post_data_hook(self, data):
        super().post_data_hook(data)
        data = self.include_values_in_labels(data)
        return data
