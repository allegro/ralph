# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from rest_framework import routers

from ralph.data_center.views.api import DataCenterAssetViewSet

router = routers.DefaultRouter()
router.register(r'data-center-assets', DataCenterAssetViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
