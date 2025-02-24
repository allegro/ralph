from rest_framework import fields, serializers

from ralph.assets.api.serializers import (
    BaseObjectSerializer,
    ComponentSerializerMixin,
    SecurityScanField
)
from ralph.assets.models import BaseObject
from ralph.data_center.api.serializers import DataCenterAssetSimpleSerializer
from ralph.data_center.models import DCHost


class DCHostSerializer(ComponentSerializerMixin, BaseObjectSerializer):
    hostname = fields.CharField()
    securityscan = SecurityScanField()
    hypervisor = DataCenterAssetSimpleSerializer(required=False)

    class Meta:
        model = DCHost
        fields = [
            "id",
            "url",
            "ethernet",
            "ipaddresses",
            "custom_fields",
            "tags",
            "securityscan",
            "object_type",
            "__str__",
            "service_env",
            "configuration_path",
            "hostname",
            "created",
            "modified",
            "remarks",
            "parent",
            "configuration_variables",
            "hypervisor",
        ]


class DCHostPhysicalSerializer(DCHostSerializer):
    model = serializers.SerializerMethodField()

    class Meta:
        model = BaseObject
        fields = DCHostSerializer.Meta.fields + ["model"]

    def get_model(self, obj):
        try:
            return str(obj.model)
        except AttributeError:
            return None
