# -*- coding: utf-8 -*-

from ralph.api import RalphAPIViewSet
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.api.serializers import (
    AccessorySerializer,
    DataCenterAssetSerializer,
    DataCenterSerializer,
    RackAccessorySerializer,
    RackSerializer,
    ServerRoomSerializer
)
from ralph.data_center.models.physical import (
    Accessory,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
)


class DataCenterAssetViewSet(RalphAPIViewSet):
    queryset = DataCenterAsset.objects.all()
    serializer_class = DataCenterAssetSerializer
    select_related = DataCenterAssetAdmin.list_select_related + [
        'service_env', 'service_env__service', 'service_env__environment',
        'rack', 'rack__server_room', 'rack__server_room__data_center',
    ]
    prefetch_related = [
        'service_env__service__environments',
        'service_env__service__business_owners',
        'service_env__service__technical_owners',
        'connections',
        'tags',
    ]


class AccessoryViewSet(RalphAPIViewSet):
    queryset = Accessory.objects.all()
    serializer_class = AccessorySerializer


class RackAccessoryViewSet(RalphAPIViewSet):
    queryset = RackAccessory.objects.all()
    serializer_class = RackAccessorySerializer


class RackViewSet(RalphAPIViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    prefetch_related = ['rackaccessory_set', 'rackaccessory_set__accessory']


class ServerRoomViewSet(RalphAPIViewSet):
    queryset = ServerRoom.objects.all()
    serializer_class = ServerRoomSerializer


class DataCenterViewSet(RalphAPIViewSet):
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer
