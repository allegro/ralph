# -*- coding: utf-8 -*-


from ralph.api import RalphAPIViewSet
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.assets.api.views import BaseObjectViewSet, BaseObjectViewSetMixin
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.api.serializers import (
    AccessorySerializer,
    BaseObjectClusterSerializer,
    ClusterSerializer,
    ClusterTypeSerializer,
    DatabaseSerializer,
    DataCenterAssetSerializer,
    DataCenterSerializer,
    RackAccessorySerializer,
    RackSerializer,
    ServerRoomSerializer,
    VIPSerializer
)
from ralph.data_center.models import (
    Accessory,
    BaseObjectCluster,
    Cluster,
    ClusterType,
    Database,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom,
    VIP
)


class DataCenterAssetFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = DataCenterAsset


class DataCenterAssetViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = DataCenterAsset.objects.all()
    serializer_class = DataCenterAssetSerializer
    select_related = DataCenterAssetAdmin.list_select_related + [
        'service_env', 'service_env__service', 'service_env__environment',
        'rack', 'rack__server_room', 'rack__server_room__data_center',
        'property_of', 'budget_info'
    ]
    prefetch_related = BaseObjectViewSet.prefetch_related + [
        'service_env__service__environments',
        'service_env__service__business_owners',
        'service_env__service__technical_owners',
        'connections',
        'tags',
    ]
    filter_fields = [
        'service_env__service__uid',
        'service_env__service__name',
        'service_env__service__id',
    ]
    additional_filter_class = DataCenterAssetFilterSet


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


class DatabaseViewSet(RalphAPIViewSet):
    queryset = Database.objects.all()
    serializer_class = DatabaseSerializer


class VIPViewSet(RalphAPIViewSet):
    queryset = VIP.objects.all()
    serializer_class = VIPSerializer


class ClusterTypeViewSet(RalphAPIViewSet):
    queryset = ClusterType.objects.all()
    serializer_class = ClusterTypeSerializer


class BaseObjectClusterViewSet(RalphAPIViewSet):
    queryset = BaseObjectCluster.objects.all()
    serializer_class = BaseObjectClusterSerializer


class ClusterViewSet(RalphAPIViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    select_related = [
        'type', 'parent', 'service_env', 'service_env__service',
        'service_env__environment',
    ]
    prefetch_related = ['tags', 'baseobjectcluster_set']
