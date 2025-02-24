# -*- coding: utf-8 -*-
from django.db.models import Prefetch
from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import (
    ServiceEnvironmentSimpleSerializer,
    StrField,
    TypeFromContentTypeSerializerMixin
)
from ralph.assets.models import BaseObject
from ralph.supports.models import BaseObjectsSupport, Support, SupportType


class SupportTypeSerializer(RalphAPISerializer):
    class Meta:
        model = SupportType
        fields = "__all__"


class SupportTypeViewSet(RalphAPIViewSet):
    queryset = SupportType.objects.all()
    serializer_class = SupportTypeSerializer


class SupportSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Support
        fields = [
            "support_type",
            "contract_id",
            "name",
            "serial_no",
            "date_from",
            "date_to",
            "created",
            "remarks",
            "description",
            "url",
        ]
        _skip_tags_field = True


class SupportSerializer(TypeFromContentTypeSerializerMixin, RalphAPISerializer):
    __str__ = StrField(show_type=True)
    base_objects = serializers.HyperlinkedRelatedField(
        many=True, view_name="baseobject-detail", read_only=True
    )
    service_env = ServiceEnvironmentSimpleSerializer()

    class Meta:
        model = Support
        depth = 1
        exclude = ("content_type", "configuration_path")


class SupportViewSet(RalphAPIViewSet):
    queryset = Support.objects.all()
    serializer_class = SupportSerializer
    select_related = [
        "region",
        "budget_info",
        "support_type",
        "property_of",
        "service_env",
        "service_env__service",
        "service_env__environment",
    ]
    prefetch_related = [
        "tags",
        Prefetch("base_objects", queryset=BaseObject.objects.all()),
    ]


class BaseObjectsSupportSerializer(RalphAPISerializer):
    support = SupportSimpleSerializer()
    baseobject = serializers.HyperlinkedRelatedField(
        view_name="baseobject-detail", read_only=True
    )

    class Meta:
        model = BaseObjectsSupport
        fields = "__all__"


class BaseObjectSupportViewSet(RalphAPIViewSet):
    queryset = BaseObjectsSupport.objects.all()
    serializer_class = BaseObjectsSupportSerializer
    select_related = ["baseobject", "support"]


router.register(r"base-objects-supports", BaseObjectSupportViewSet)
router.register(r"supports", SupportViewSet)
router.register(r"support-types", SupportTypeViewSet)
urlpatterns = []
