# -*- coding: utf-8 -*-

from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.api.serializers import (
    AssetSerializer,
    BaseObjectSerializer,
    ComponentSerializerMixin,
    NetworkComponentSerializerMixin,
    OwnersFromServiceEnvSerializerMixin,
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
)


class ClusterTypeSerializer(RalphAPISerializer):
    class Meta:
        model = ClusterType
        depth = 1
        fields = "__all__"


class ClusterSimpleSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Cluster
        exclude = ("content_type",)
        depth = 1


class BaseObjectClusterSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = BaseObjectCluster
        fields = ("id", "url", "base_object", "is_master")


class BaseObjectClusterSerializer(RalphAPISerializer):
    class Meta:
        model = BaseObjectCluster
        fields = ("id", "url", "base_object", "is_master", "cluster")


class ClusterSerializer(
    NetworkComponentSerializerMixin,
    OwnersFromServiceEnvSerializerMixin,
    ClusterSimpleSerializer,
):
    base_objects = BaseObjectClusterSimpleSerializer(
        many=True, read_only=True, source="baseobjectcluster_set"
    )
    masters = serializers.HyperlinkedRelatedField(
        many=True, view_name="baseobject-detail", read_only=True, source="get_masters"
    )

    class Meta(ClusterSimpleSerializer.Meta):
        exclude = (
            "parent",
            "content_type",
        )


class DataCenterSerializer(RalphAPISerializer):
    class Meta:
        model = DataCenter
        depth = 1
        fields = "__all__"


class ServerRoomSerializer(RalphAPISerializer):
    class Meta:
        model = ServerRoom
        depth = 1
        fields = "__all__"


class AccessorySerializer(RalphAPISerializer):
    class Meta:
        model = Accessory
        fields = "__all__"


class RackAccessorySerializer(RalphAPISerializer):
    name = serializers.ReadOnlyField(source="accessory.name")

    class Meta:
        model = RackAccessory
        fields = "__all__"


class SimpleRackSerializer(RalphAPISerializer):
    class Meta:
        model = Rack
        depth = 2
        exclude = ("accessories",)


class RackSerializer(RalphAPISerializer):
    accessories = RackAccessorySerializer(
        read_only=True, many=True, source="rackaccessory_set"
    )

    class Meta(SimpleRackSerializer.Meta):
        model = Rack
        depth = 2
        exclude = ()


class DataCenterAssetSimpleSerializer(RalphAPISerializer):
    hostname = serializers.SerializerMethodField()

    def get_hostname(self, obj):
        match obj:
            case DataCenterAsset():
                return obj.hostname
            case _:
                try:
                    return self.context.get("parent_obj").parent_hostname
                except AttributeError:
                    return None

    class Meta:
        model = DataCenterAsset
        fields = ["id", "hostname", "url"]
        _skip_tags_field = True


class DataCenterAssetSerializer(ComponentSerializerMixin, AssetSerializer):
    rack = SimpleRackSerializer()
    related_hosts = serializers.SerializerMethodField()
    support_end_date = serializers.DateField(required=False, allow_null=True)

    def get_related_hosts(self, obj):
        from ralph.virtual.api import (
            CloudHostSimpleSerializer,
            VirtualServerSimpleSerializer,
        )

        # attributes "virtual_servers", "physical_servers" and "cloud_hosts"
        # are custom prefetches, see DataCenterAssetViewSet
        return {
            "virtual_servers": VirtualServerSimpleSerializer(
                obj.virtual_servers, many=True, context=self.context
            ).data,
            "physical_servers": DataCenterAssetSimpleSerializer(
                obj.physical_servers, many=True, context=self.context
            ).data,
            "cloud_hosts": CloudHostSimpleSerializer(
                obj.cloud_hosts, many=True, context=self.context
            ).data,
        }

    class Meta(AssetSerializer.Meta):
        model = DataCenterAsset
        depth = 2


class DataCenterAssetSaveSerializer(RalphAPISaveSerializer):
    rack = serializers.PrimaryKeyRelatedField(
        allow_null=False, required=True, queryset=Rack.objects.all()
    )

    class Meta:
        model = DataCenterAsset
        fields = "__all__"


class DatabaseSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Database
        depth = 1
