# -*- coding: utf-8 -*-
from django.conf.urls import include
from django.urls import re_path

from ralph.api.tests import api as ralph_api
from ralph.lib.custom_fields.tests import urls as custom_fields_tests_urls
from ralph.lib.permissions.tests import api as lib_api
from ralph.lib.permissions.tests.test_permission_view import urls as perm_view_url  # noqa
from ralph.urls.base import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns
urlpatterns += [
    re_path(r"^", include(lib_api.urlpatterns)),
    re_path(r"^", include(perm_view_url)),
    re_path(r"^", include(ralph_api.urlpatterns)),
    re_path(r"^", include(custom_fields_tests_urls.urlpatterns)),
]
