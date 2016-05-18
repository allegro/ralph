from django.conf import settings
from django.conf.urls import include, url
from rest_framework.authtoken import views

from ralph.admin import ralph_site as admin
from ralph.api import router

# import custom urls from each api module
# notice that each module should have `urlpatters` variable defined
# (as empty list if there is any custom url)
api_urls = list(map(lambda u: url(r'^', include(u)), [
    'ralph.accounts.api',
    'ralph.assets.api.routers',
    'ralph.back_office.api',
    'ralph.data_center.api.routers',
    'ralph.dc_view.urls.api',
    'ralph.domains.api',
    'ralph.supports.api',
    'ralph.security.api',
    'ralph.virtual.api',
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
]

if getattr(settings, 'ENABLE_HERMES_INTEGRATION', False):
    urlpatterns += url(r'^hermes/', include('pyhermes.apps.django.urls')),
