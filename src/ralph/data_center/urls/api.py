# -*- coding: utf-8 -*-
from ralph.api import router
from ralph.data_center.views.api import DataCenterAssetViewSet

router.register(r'data-center-assets', DataCenterAssetViewSet)
urlpatterns = []
