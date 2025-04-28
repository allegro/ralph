from django.urls import re_path

from ralph.dashboards.views import DashboardView

urlpatterns = [
    re_path(
        r"^dashboard_view/(?P<dashboard_id>\d+)/$",
        DashboardView.as_view(),
        name="dashboard_view",
    ),
]
