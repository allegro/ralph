# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import url

from ralph.dc_view.views.api import (
    DCAssetsView,
    DCRacksAPIView
)


urlpatterns = [
    url(
        r'^rack/?$',
        DCAssetsView.as_view(),
    ),
    url(
        r'^rack/(?P<rack_id>\d+)/?$',
        DCAssetsView.as_view(),
    ),
    url(
        r'^data_center/(?P<data_center_id>\d+)/?$',
        DCRacksAPIView.as_view(),
    ),
]
