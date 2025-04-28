from django.conf.urls import include
from django.urls import re_path

from . import admin, api

urlpatterns = [
    re_path(r"^cf_tests_admin/", admin.site.urls),
    re_path(r"^cf_test_api/", include(api.urlpatterns)),
]
