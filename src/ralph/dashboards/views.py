from django.views.generic import TemplateView

from ralph.dashboards.models import Dashboard


class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

    def dispatch(self, request, dashboard_id, *args, **kwargs):
        self.dashboard = Dashboard.objects.get(id=dashboard_id, active=True)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        kwargs["graphs"] = []
        rendered_graphs = ""
        for graph in self.dashboard.graphs.filter(active=True).order_by("pk"):
            rendered_graphs += graph.render(
                name="dashboard_{}_graph_{}".format(self.dashboard.id, graph.id)
            )
        kwargs["name"] = self.dashboard.name
        kwargs["interval"] = self.dashboard.interval
        kwargs["description"] = self.dashboard.description
        kwargs["rendered_graphs"] = rendered_graphs
        return super().get(request, *args, **kwargs)
