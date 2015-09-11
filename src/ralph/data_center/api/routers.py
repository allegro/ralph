# -*- coding: utf-8 -*-
from ralph.api import router
from ralph.data_center.api.views import (
    AccessoryViewSet,
    DataCenterAssetViewSet,
    DataCenterViewSet,
    RackAccessoryViewSet,
    RackViewSet,
    ServerRoomViewSet
)

router.register(r'accessories', AccessoryViewSet)
router.register(r'data-centers', DataCenterViewSet)
router.register(r'data-center-assets', DataCenterAssetViewSet)
router.register(r'racks', RackViewSet)
router.register(r'rack-accessories', RackAccessoryViewSet)
router.register(r'server-rooms', ServerRoomViewSet)
urlpatterns = []
