# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType

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
from ralph.virtual.models import VirtualServer


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
    related_hosts = serializers.SerializerMethodField()

    def _get_serialized_sublist(self, full_list, serializer_class, cond):
        return serializer_class(
            [elem for elem in full_list if cond(elem)],
            many=True, context=self.context
        ).data

    def _get_physical_servers(self, obj):
        dca = ContentType.objects.get_for_model(DataCenterAsset)
        return self._get_serialized_sublist(
            obj.children.all(),
            DataCenterAssetSimpleSerializer,
            lambda child: child.content_type == dca
        )

    def _get_virtual_servers(self, obj):
        from ralph.virtual.api import VirtualServerSimpleSerializer
        vs = ContentType.objects.get_for_model(VirtualServer)
        return self._get_serialized_sublist(
            obj.children.all(),
            VirtualServerSimpleSerializer,
            lambda child: child.content_type == vs
        )

    def _get_cloud_hosts(self, obj):
        from ralph.virtual.api import CloudHostSimpleSerializer
        return self._get_serialized_sublist(
            obj.cloudhost_set.all(),
            CloudHostSimpleSerializer,
            lambda host: True
        )

    def get_related_hosts(self, obj):
        related_hosts = {}
        related_hosts['virtual_servers'] = self._get_virtual_servers(obj)
        related_hosts['physical_servers'] = self._get_physical_servers(obj)
        related_hosts['cloud_hosts'] = self._get_cloud_hosts(obj)
        return related_hosts

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
