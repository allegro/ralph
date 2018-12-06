from django.conf import settings
from django.conf.urls import include, url
from rest_framework.authtoken import views
from sitetree.sitetreeapp import SiteTree  # noqa

from ralph.admin import ralph_site as admin
from ralph.api import router
from ralph.health_check import status_health, status_ping

# monkey patch for sitetree until
# https://github.com/idlesign/django-sitetree/issues/226 will be discussed
# and resolved
SiteTree.current_app_is_admin = lambda self: False

# import custom urls from each api module
# notice that each module should have `urlpatters` variable defined
# (as empty list if there is any custom url)
api_urls = list(map(lambda u: url(r'^', include(u)), [
    'ralph.accounts.api',
    'ralph.assets.api.routers',
    'ralph.back_office.api',
    'ralph.configuration_management.api',
    'ralph.dashboards.api.routers',
    'ralph.data_center.api.routers',
    'ralph.dc_view.urls.api',
    'ralph.dhcp.api',
    'ralph.domains.api',
    'ralph.operations.api',
    'ralph.supports.api',
    'ralph.security.api',
    'ralph.sim_cards.api',
    'ralph.networks.api',
    'ralph.virtual.api',
    'ralph.lib.custom_fields.api.custom_fields_api',
    'ralph.lib.transitions.api.routers'
]))
# include router urls
# because we're using single router instance and urls are cached inside this
# object, router.urls may be called after all urls are processed (and all
# api views are registered in router)
api_urls += [url(r'^', include(router.urls))]

urlpatterns = [
    url(r'^', include(admin.urls)),
    url(r'^api/', include(api_urls)),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^', include('ralph.dc_view.urls.ui')),
    url(r'^', include('ralph.attachments.urls')),
    url(r'^', include('ralph.dashboards.urls')),
    url(r'^', include('ralph.accounts.urls')),
    url(r'^', include('ralph.reports.urls')),
    url(r'^', include('ralph.admin.autocomplete_urls')),
    url(r'^dhcp/', include('ralph.dhcp.urls')),
    url(r'^deployment/', include('ralph.deployment.urls')),
    url(r'^virtual/', include('ralph.virtual.urls')),
    url(r'^', include('ralph.lib.transitions.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(
        r'^status/ping?$',
        status_ping,
        name='status-ping',
    ),
    url(
        r'^status/health?$',
        status_health,
        name='status-health',
    ),
]

if getattr(settings, 'ENABLE_HERMES_INTEGRATION', False):
    urlpatterns += url(r'^hermes/', include('pyhermes.apps.django.urls')),
