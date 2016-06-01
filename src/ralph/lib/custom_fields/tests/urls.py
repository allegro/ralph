from django.conf.urls import include, url

from . import admin, api

urlpatterns = [
    url(r'^cf_tests_admin/', include(admin.site.urls)),
    url(r'^cf_test_api/', include(api.urlpatterns))
]
