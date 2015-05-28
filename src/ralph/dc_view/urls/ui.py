# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import url

from ralph.dc_view.views.ui import DataCenterView


urlpatterns = [
    url(
        r'^dc_view/?$',
        DataCenterView.as_view(),
        name='dc_view'
    ),
]
