# -*- coding: utf-8 -*-
import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from rest_framework import serializers

from django.urls import reverse

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import (
    ServiceEnvironmentSimpleSerializer,
    StrField,
    TypeFromContentTypeSerializerMixin,
)
from ralph.assets.models import BaseObject
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models import DataCenterAsset
from ralph.lib.permissions.api import PermissionsForObjectFilter
from ralph.lib.visibility_scope.filters import visibility_scope_asset_support_filter
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


class BackOfficeAssetForSupportSerializer(RalphAPISerializer):
    id = serializers.IntegerField(source="pk")
    model = serializers.CharField(source="model.name", read_only=True)
    manufacturer = serializers.CharField(source="model.manufacturer.name", read_only=True)
    category = serializers.CharField(source="model.category.name", read_only=True)
    service_env = ServiceEnvironmentSimpleSerializer(read_only=True)
    property_of = serializers.CharField(source="property_of.name", read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BackOfficeAsset
        fields = [
            "id",
            "barcode",
            "sn",
            "hostname",
            "model",
            "manufacturer",
            "category",
            "status",
            "service_env",
            "property_of",
            "order_no",
        ]
        _skip_tags_field = True


class DataCenterAssetForSupportSerializer(RalphAPISerializer):
    id = serializers.IntegerField(source="pk")
    model = serializers.CharField(source="model.name", read_only=True)
    manufacturer = serializers.CharField(source="model.manufacturer.name", read_only=True)
    category = serializers.CharField(source="model.category.name", read_only=True)
    service_env = ServiceEnvironmentSimpleSerializer(read_only=True)
    property_of = serializers.CharField(source="property_of.name", read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DataCenterAsset
        fields = [
            "id",
            "barcode",
            "sn",
            "hostname",
            "model",
            "manufacturer",
            "category",
            "status",
            "service_env",
            "property_of",
            "order_no",
        ]
        _skip_tags_field = True


class SupportSerializer(TypeFromContentTypeSerializerMixin, RalphAPISerializer):
    __str__ = StrField(show_type=True)
    base_objects = serializers.SerializerMethodField()
    service_env = ServiceEnvironmentSimpleSerializer()
    backoffice_assets = serializers.SerializerMethodField()
    datacenter_assets = serializers.SerializerMethodField()

    def get_base_objects(self, obj):
        request = self.context.get('request')
        base_objects = [bos.baseobject for bos in obj.baseobjectssupport_set.all()]
        return [
            request.build_absolute_uri(
                reverse('baseobject-detail', kwargs={'pk': bo.pk})
            )
            for bo in base_objects
        ]

    class Meta:
        model = Support
        depth = 1
        exclude = ("content_type", "configuration_path")

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and not request.query_params.get('include_assets'):
            fields.pop('backoffice_assets', None)
            fields.pop('datacenter_assets', None)
        return fields

    def get_backoffice_assets(self, obj):
        request = self.context.get('request')
        if not request or not request.query_params.get('include_assets'):
            return []

        backoffice_ct_id = ContentType.objects.get_for_model(BackOfficeAsset).id

        backoffice_assets = [
            bos.baseobject for bos in obj.baseobjectssupport_set.all()
            if bos.baseobject.content_type_id == backoffice_ct_id
        ]
        return BackOfficeAssetForSupportSerializer(backoffice_assets, many=True).data

    def get_datacenter_assets(self, obj):
        request = self.context.get('request')
        if not request or not request.query_params.get('include_assets'):
            return []

        datacenter_ct_id = ContentType.objects.get_for_model(DataCenterAsset).id

        datacenter_assets = [
            bos.baseobject for bos in obj.baseobjectssupport_set.all()
            if bos.baseobject.content_type_id == datacenter_ct_id
        ]
        return DataCenterAssetForSupportSerializer(datacenter_assets, many=True).data


class BaseObjectsFilter(django_filters.FilterSet):
    """
    select supports that are assigned to one of the assets
    e.g. /?base_objects=1,2,3

    """

    base_objects = django_filters.CharFilter(
        field_name="base_objects", method="filter_base_objects"
    )

    class Meta:
        model = Support
        fields = ("base_objects",)

    def filter_base_objects(self, queryset, name, value):
        if not value:
            return queryset
        try:
            ids = [int(x) for x in value.split(",")]
            return queryset.filter(base_objects__in=ids)
        except ValueError:
            return queryset.none()


class SupportViewSet(RalphAPIViewSet):
    queryset = Support.objects.all()
    serializer_class = SupportSerializer
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        PermissionsForObjectFilter,
    )
    filterset_class = BaseObjectsFilter
    select_related = [
        "content_type",
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
    ]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.query_params.get("include_assets"):
            queryset = queryset.prefetch_related(
                Prefetch(
                    "baseobjectssupport_set__baseobject",
                    queryset=BaseObject.polymorphic_objects.select_related(
                        "content_type"
                    ).polymorphic_select_related(
                        BackOfficeAsset=[
                            "model",
                            "model__manufacturer",
                            "model__category",
                            "service_env",
                            "service_env__service",
                            "service_env__environment",
                            "property_of",
                        ],
                        DataCenterAsset=[
                            "model",
                            "model__manufacturer",
                            "model__category",
                            "service_env",
                            "service_env__service",
                            "service_env__environment",
                            "property_of",
                        ],
                    ),
                )
            )
        else:
            queryset = queryset.prefetch_related(
                Prefetch(
                    "baseobjectssupport_set__baseobject",
                    queryset=BaseObject.polymorphic_objects.all(),
                )
            )
        return queryset


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
    extended_filter_fields = {
        "base_object": ["baseobject"],
    }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(visibility_scope_asset_support_filter(self.request.user))
        )


router.register(r"base-objects-supports", BaseObjectSupportViewSet)
router.register(r"supports", SupportViewSet)
router.register(r"support-types", SupportTypeViewSet)
urlpatterns = []
