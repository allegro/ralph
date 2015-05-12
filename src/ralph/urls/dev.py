# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import include, url

import debug_toolbar

from ralph.urls import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns
urlpatterns += [
    url(r'^__debug__/', include(debug_toolbar.urls)),
]
