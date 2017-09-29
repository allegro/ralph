# -*- coding: utf-8 -*-
from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.api.serializers import (
    AssetSerializer,
    BaseObjectSerializer,
    ComponentSerializerMixin,
    NetworkComponentSerializerMixin,
    OwnersFromServiceEnvSerializerMixin
)
from ralph.configuration_management.api import SCMInfoSerializer
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
from ralph.security.api import SecurityScanSerializer


class ClusterTypeSerializer(RalphAPISerializer):
    class Meta:
        model = ClusterType
        depth = 1


class ClusterSimpleSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Cluster
        exclude = ('content_type',)
        depth = 1


class BaseObjectClusterSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = BaseObjectCluster
        fields = ('id', 'url', 'base_object', 'is_master')


class BaseObjectClusterSerializer(RalphAPISerializer):
    class Meta:
        model = BaseObjectCluster
        fields = ('id', 'url', 'base_object', 'is_master', 'cluster')


class ClusterSerializer(
    NetworkComponentSerializerMixin,
    OwnersFromServiceEnvSerializerMixin,
    ClusterSimpleSerializer
):
    base_objects = BaseObjectClusterSimpleSerializer(
        many=True, read_only=True, source='baseobjectcluster_set'
    )
    masters = serializers.HyperlinkedRelatedField(
        many=True, view_name='baseobject-detail', read_only=True,
        source='get_masters'
    )

    class Meta(ClusterSimpleSerializer.Meta):
        exclude = ('parent', 'content_type',)


class DataCenterSerializer(RalphAPISerializer):
    class Meta:
        model = DataCenter
        depth = 1


class ServerRoomSerializer(RalphAPISerializer):
    class Meta:
        model = ServerRoom
        depth = 1


class AccessorySerializer(RalphAPISerializer):
    class Meta:
        model = Accessory


class RackAccessorySerializer(RalphAPISerializer):
    name = serializers.ReadOnlyField(source='accessory.name')

    class Meta:
        model = RackAccessory


class SimpleRackSerializer(RalphAPISerializer):
    class Meta:
        model = Rack
        depth = 2
        exclude = ('accessories',)


class RackSerializer(RalphAPISerializer):
    accessories = RackAccessorySerializer(
        read_only=True, many=True, source='rackaccessory_set'
    )

    class Meta(SimpleRackSerializer.Meta):
        model = Rack
        depth = 2
        exclude = ()


class DataCenterAssetSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = DataCenterAsset
        fields = ['hostname', 'url']
        _skip_tags_field = True


class DataCenterAssetSerializer(ComponentSerializerMixin, AssetSerializer):
    rack = SimpleRackSerializer()
    scmstatuscheck = SCMInfoSerializer()
    securityscan = SecurityScanSerializer()

    class Meta(AssetSerializer.Meta):
        model = DataCenterAsset
        depth = 2


class DataCenterAssetSaveSerializer(RalphAPISaveSerializer):
    rack = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=Rack.objects.all()
    )

    class Meta(object):
        model = DataCenterAsset


class DatabaseSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Database
        depth = 1


class VIPSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = VIP
        depth = 1
