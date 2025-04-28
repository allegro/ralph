from django.conf import settings
from django.conf.urls import include
from django.urls import path, re_path
from django_prometheus import exports
from rest_framework.authtoken import views
from sitetree.sitetreeapp import SiteTree  # noqa

from ralph.admin.sites import ralph_site as admin
from ralph.api import router
from ralph.health_check import status_health, status_ping

# monkey patch for sitetree until
# https://github.com/idlesign/django-sitetree/issues/226 will be discussed
# and resolved
SiteTree.current_app_is_admin = lambda self: False

# import custom urls from each api module
# notice that each module should have `urlpatters` variable defined
# (as empty list if there is any custom url)
api_urls = list(
    map(
        lambda u: re_path(r"^", include(u)),
        [
            "ralph.access_cards.api",
            "ralph.accounts.api",
            "ralph.assets.api.routers",
            "ralph.back_office.api",
            "ralph.dashboards.api.routers",
            "ralph.data_center.api.routers",
            "ralph.dc_view.urls.api",
            "ralph.dhcp.api",
            "ralph.domains.api",
            "ralph.operations.api",
            "ralph.supports.api",
            "ralph.sim_cards.api",
            "ralph.ssl_certificates.api",
            "ralph.networks.api",
            "ralph.virtual.api",
            "ralph.lib.custom_fields.api.custom_fields_api",
            "ralph.lib.transitions.api.routers",
            "ralph.lib.visibility_scope.api",
        ],
    )
)
# include router urls
# because we're using single router instance and urls are cached inside this
# object, router.urls may be called after all urls are processed (and all
# api views are registered in router)
api_urls += [re_path(r"^", include(router.urls))]

urlpatterns = [
    re_path(r"^api/", include(api_urls)),
    re_path(r"^", admin.urls),
    re_path(r"^api-token-auth/", views.obtain_auth_token),
    re_path(r"^", include("ralph.dc_view.urls.ui")),
    re_path(r"^", include("ralph.attachments.urls")),
    re_path(r"^", include("ralph.dashboards.urls")),
    re_path(r"^", include("ralph.accounts.urls")),
    re_path(r"^", include("ralph.reports.urls")),
    re_path(r"^", include("ralph.admin.autocomplete_urls")),
    re_path(r"^dhcp/", include("ralph.dhcp.urls")),
    re_path(r"^deployment/", include("ralph.deployment.urls")),
    re_path(r"^virtual/", include("ralph.virtual.urls")),
    re_path(r"^", include("ralph.lib.transitions.urls")),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    re_path(
        r"^status/ping?$",
        status_ping,
        name="status-ping",
    ),
    re_path(
        r"^status/health?$",
        status_health,
        name="status-health",
    ),
]

if getattr(settings, "ENABLE_HERMES_INTEGRATION", False):
    urlpatterns += (re_path(r"^hermes/", include("pyhermes.apps.django.urls")),)

if getattr(settings, "PROMETHEUS_METRICS_ENABLED", False):
    urlpatterns += [
        path(
            "status/prometheus",
            exports.ExportToDjangoView,
            name="status-prometheus",
        )
    ]
