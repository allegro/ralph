from django.conf.urls import include, url

from ralph.admin import ralph_site as admin

urlpatterns = [
    url(r'^', include(admin.urls)),
    url(r'^api/', include('ralph.dc_view.urls.api')),
    url(r'^api/', include('ralph.data_center.urls.api')),
    url(r'^', include('ralph.dc_view.urls.ui')),
    url(r'^', include('ralph.reports.urls')),
]
