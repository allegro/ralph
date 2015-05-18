# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import include, url

from ralph.admin import ralph_site as admin

urlpatterns = [
    url(r'^admin/', include(admin.urls)),
]
