from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from ralph.dashboards.helpers import decode_params
from ralph.dashboards.models import Graph
from ralph.dashboards.renderers import GRAPH_QUERY_SEP


class ByGraphFilter(admin.SimpleListFilter):
    title = _("Graph ID")
    parameter_name = "graph-query"
    sep = GRAPH_QUERY_SEP
    template = "admin/filters/by-graph.html"

    def lookups(self, request, model_admin):
        return (("", ""),)

    def queryset(self, request, queryset):
        params = decode_params(self.value())
        graph_pk = params.get("pk")
        filters = params.get("filters")
        if graph_pk:
            graph = get_object_or_404(Graph, pk=graph_pk)
            queryset = graph.get_queryset_for_filter(queryset, filters)
        return queryset
