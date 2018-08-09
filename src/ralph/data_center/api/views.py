# -*- coding: utf-8 -*-
from django.db.models import Prefetch

from ralph.api import RalphAPIViewSet
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.assets.api.views import (
    base_object_descendant_prefetch_related,
    BaseObjectViewSetMixin
)
from ralph.assets.models import Ethernet
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.api.serializers import (
    AccessorySerializer,
    BaseObjectClusterSerializer,
    ClusterSerializer,
    ClusterTypeSerializer,
    DatabaseSerializer,
    DataCenterAssetSaveSerializer,
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
from ralph.security.models import SecurityScan


class DataCenterAssetFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = DataCenterAsset


class DataCenterAssetViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = DataCenterAsset.objects.all()
    serializer_class = DataCenterAssetSerializer
    save_serializer_class = DataCenterAssetSaveSerializer
    select_related = DataCenterAssetAdmin.list_select_related + [
        'service_env', 'service_env__service', 'service_env__environment',
        'rack', 'rack__server_room', 'rack__server_room__data_center',
        'property_of', 'budget_info', 'content_type',
        'configuration_path__module',
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        'connections',
        'tags',
        'memory_set',
        'children',
        'cloudhost_set',
        Prefetch(
            'ethernet_set',
            queryset=Ethernet.objects.select_related('ipaddress')
        ),
        Prefetch(
            'securityscan',
            queryset=SecurityScan.objects.prefetch_related(
                'vulnerabilities', 'tags'
            )
        ),
        'fibrechannelcard_set',
        'processor_set',
        'disk_set',
    ]
    filter_fields = [
        'service_env__service__uid',
        'service_env__service__name',
        'service_env__service__id',
        'service_env__environment__name',
        'firmware_version',
        'bios_version',
    ]
    additional_filter_class = DataCenterAssetFilterSet
    exclude_filter_fields = ['configuration_path']


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


class ClusterFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = Cluster


class ClusterViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    select_related = [
        'type', 'parent', 'service_env', 'service_env__service',
        'service_env__environment', 'configuration_path__module', 'content_type'
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        'tags', 'baseobjectcluster_set__base_object',
        Prefetch(
            'ethernet_set',
            queryset=Ethernet.objects.select_related('ipaddress')
        ),
    ]
    additional_filter_class = ClusterFilterSet
