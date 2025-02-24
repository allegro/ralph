# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from ralph.api import RalphAPIViewSet
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.assets.api.views import (
    base_object_descendant_prefetch_related,
    BaseObjectViewSetMixin
)
from ralph.assets.models import (
    ConfigurationClass,
    ConfigurationModule,
    Ethernet,
    ServiceEnvironment
)
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
from ralph.virtual.models import CloudHost, VirtualServer


class DataCenterAssetFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = DataCenterAsset


class DataCenterAssetViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = DataCenterAsset.objects.all()
    serializer_class = DataCenterAssetSerializer
    save_serializer_class = DataCenterAssetSaveSerializer
    select_related = DataCenterAssetAdmin.list_select_related + [
        "rack__server_room__data_center",
        "property_of",
        "budget_info",
        "content_type",
        "configuration_path__module",
        "securityscan",
        "baseobject_ptr",
        "asset_ptr",
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        Prefetch(
            "children",
            queryset=VirtualServer.objects.select_related("parent"),
            to_attr="virtual_servers",
        ),
        Prefetch(
            "children",
            queryset=DataCenterAsset.objects.select_related("parent"),
            to_attr="physical_servers",
        ),
        "rack__server_room__data_center",
        "connections",
        "tags",
        "memory_set",
        Prefetch(
            "cloudhost_set",
            queryset=CloudHost.objects.select_related("parent"),
            to_attr="cloud_hosts",
        ),
        Prefetch("ethernet_set", queryset=Ethernet.objects.select_related("ipaddress")),
        "fibrechannelcard_set",
        "processor_set",
        "disk_set",
    ]
    filter_fields = [
        "service_env__service__uid",
        "service_env__service__name",
        "service_env__service__id",
        "service_env__environment__name",
        "firmware_version",
        "bios_version",
    ]
    additional_filter_class = DataCenterAssetFilterSet
    exclude_filter_fields = ["configuration_path"]

    def get_queryset(self):
        # precache content types, this can save 3 db queries occasionally
        ContentType.objects.get_for_models(
            DataCenterAsset, ConfigurationClass, ConfigurationModule, ServiceEnvironment
        )
        qs = super().get_queryset()
        return qs


class AccessoryViewSet(RalphAPIViewSet):
    queryset = Accessory.objects.all()
    serializer_class = AccessorySerializer


class RackAccessoryViewSet(RalphAPIViewSet):
    queryset = RackAccessory.objects.all()
    serializer_class = RackAccessorySerializer


class RackViewSet(RalphAPIViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    prefetch_related = ["rackaccessory_set", "rackaccessory_set__accessory"]


class ServerRoomViewSet(RalphAPIViewSet):
    queryset = ServerRoom.objects.all()
    serializer_class = ServerRoomSerializer


class DataCenterViewSet(RalphAPIViewSet):
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer


class DatabaseViewSet(RalphAPIViewSet):
    queryset = Database.objects.all()
    serializer_class = DatabaseSerializer
    prefetch_related = (
        "tags",
        "licences",
        "custom_fields",
        "content_type",
        "service_env__service",
        "service_env__environment",
    )


class VIPViewSet(RalphAPIViewSet):
    prefetch_related = ("licences__tags", "tags", "custom_fields", "content_type")
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
        "type",
        "parent",
        "service_env",
        "service_env__service",
        "service_env__environment",
        "configuration_path__module",
        "content_type",
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        "tags",
        "baseobjectcluster_set__base_object",
        Prefetch("ethernet_set", queryset=Ethernet.objects.select_related("ipaddress")),
    ]
    additional_filter_class = ClusterFilterSet
