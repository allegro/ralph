from collections import OrderedDict

from django.urls import reverse
from rest_framework import serializers

from ralph.data_center.models.choices import RackOrientation
from ralph.data_center.models.physical import (
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
)

TYPE_EMPTY = "empty"
TYPE_ACCESSORY = "accessory"
TYPE_ASSET = "asset"
TYPE_PDU = "pdu"


class AdminLinkMixin(serializers.ModelSerializer):
    """
    A field that returns object's admin url
    """

    def admin_link(self, obj):
        if isinstance(obj, OrderedDict):
            return ""
        return reverse(
            "admin:{app_label}_{model_name}_change".format(
                app_label=obj._meta.app_label,
                model_name=obj._meta.model_name,
            ),
            args=(obj.id,),
        )


class DataCenterAssetSerializerBase(serializers.ModelSerializer):
    model = serializers.CharField(source="model.name")
    service = serializers.SerializerMethodField("get_service_env")
    orientation = serializers.CharField(source="get_orientation_desc")
    url = serializers.CharField(source="get_absolute_url")

    def get_service_env(self, obj):
        try:
            service_name = obj.service_env.service.name
        except AttributeError:
            service_name = ""
        return str(service_name)

    def get_orientation_desc(self, obj):
        return obj.get_orientation_desc()


class ServerRoomtSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerRoom
        fields = ("id", "name")


class RelatedAssetSerializer(DataCenterAssetSerializerBase):
    class Meta:
        model = DataCenterAsset
        fields = (
            "id",
            "model",
            "barcode",
            "sn",
            "slot_no",
            "hostname",
            "service",
            "orientation",
            "url",
        )


class DataCenterAssetSerializer(DataCenterAssetSerializerBase):
    category = serializers.CharField(source="model.category.name")
    height = serializers.FloatField(source="model.height_of_device")
    front_layout = serializers.CharField(source="model.get_front_layout_class")
    back_layout = serializers.CharField(source="model.get_back_layout_class")
    children = RelatedAssetSerializer(
        source="get_related_assets",
        many=True,
    )
    _type = serializers.SerializerMethodField("get_type")
    management_ip = serializers.SerializerMethodField("get_management")
    orientation = serializers.SerializerMethodField("get_orientation_desc")
    url = serializers.CharField(source="get_absolute_url")

    def get_type(self, obj):
        return TYPE_ASSET

    def get_management(self, obj):
        return obj.management_ip or ""

    class Meta:
        model = DataCenterAsset
        fields = (
            "id",
            "model",
            "category",
            "height",
            "front_layout",
            "back_layout",
            "barcode",
            "sn",
            "position",
            "children",
            "_type",
            "hostname",
            "management_ip",
            "orientation",
            "service",
            "remarks",
            "url",
        )


class RackAccessorySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="accessory.name")
    _type = serializers.SerializerMethodField("get_type")
    orientation = serializers.SerializerMethodField("get_orientation_desc")
    url = serializers.CharField(source="get_absolute_url")

    def get_type(self, obj):
        return TYPE_ACCESSORY

    def get_orientation_desc(self, obj):
        return obj.get_orientation_desc()

    class Meta:
        model = RackAccessory
        fields = ("position", "orientation", "remarks", "type", "_type", "url")


class PDUSerializer(serializers.ModelSerializer):
    model = serializers.CharField(source="model.name")
    orientation = serializers.CharField(source="get_orientation_desc")
    url = serializers.CharField(source="get_absolute_url")

    def get_type(self, obj):
        return TYPE_PDU

    class Meta:
        model = DataCenterAsset
        fields = ("model", "sn", "orientation", "url")


class RackBaseSerializer(serializers.ModelSerializer):
    free_u = serializers.IntegerField(source="get_free_u", read_only=True)
    orientation = serializers.CharField(source="get_orientation_desc")

    class Meta:
        model = Rack
        fields = (
            "id",
            "name",
            "server_room",
            "max_u_height",
            "visualization_col",
            "visualization_row",
            "free_u",
            "description",
            "orientation",
            "reverse_ordering",
        )

    def update(self, data):
        data["server_room"] = ServerRoom.objects.get(pk=data["server_room"])
        data["orientation"] = RackOrientation.id_from_name(data["orientation"])
        return super(RackBaseSerializer, self).update(self.instance, data)

    def create(self, data):
        data["orientation"] = RackOrientation.id_from_name(data["orientation"])
        data["server_room"] = ServerRoom.objects.get(pk=int(data["server_room"]))
        return Rack.objects.create(**data)


class RackSerializer(AdminLinkMixin, RackBaseSerializer):
    rack_admin_url = serializers.SerializerMethodField("admin_link")

    class Meta(RackBaseSerializer.Meta):
        fields = RackBaseSerializer.Meta.fields + ("rack_admin_url",)


class SRSerializer(AdminLinkMixin, serializers.ModelSerializer):
    rack_set = RackSerializer(source="racks", many=True)
    admin_link = serializers.SerializerMethodField("admin_link")

    class Meta:
        model = ServerRoom
        fields = (
            "id",
            "name",
            "visualization_cols_num",
            "visualization_rows_num",
            "rack_set",
            "admin_link",
        )
        depth = 1
