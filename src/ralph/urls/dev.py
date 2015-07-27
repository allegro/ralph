import debug_toolbar
from django.conf.urls import include, url

from ralph.urls import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns
urlpatterns += [
    url(r'^__debug__/', include(debug_toolbar.urls)),
]
