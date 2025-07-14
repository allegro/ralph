# -*- coding: utf-8 -*-
import django_filters
from django.db.models import Prefetch
from django_filters import Filter
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import SAFE_METHODS

import ralph.assets.api.serializers_dchosts
from ralph.api import RalphAPIViewSet
from ralph.api.filters import BooleanFilter
from ralph.api.utils import PolymorphicViewSetMixin
from ralph.assets import models
from ralph.assets.api import serializers
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.assets.models import BaseObject
from ralph.data_center.models import Cluster, DataCenterAsset
from ralph.lib.api.utils import renderer_classes_without_form
from ralph.lib.visibility_scope.filters import visibility_scope_filter
from ralph.licences.api import BaseObjectLicenceViewSet
from ralph.licences.models import BaseObjectLicence
from ralph.networks.models import IPAddress
from ralph.virtual.models import CloudHost, VirtualServer


class BusinessSegmentViewSet(RalphAPIViewSet):
    queryset = models.BusinessSegment.objects.all()
    serializer_class = serializers.BusinessSegmentSerializer


class ProfitCenterViewSet(RalphAPIViewSet):
    queryset = models.ProfitCenter.objects.all()
    serializer_class = serializers.ProfitCenterSerializer


class BudgetInfoViewSet(RalphAPIViewSet):
    queryset = models.BudgetInfo.objects.all()
    serializer_class = serializers.BudgetInfoSerializer


class EnvironmentViewSet(RalphAPIViewSet):
    queryset = models.Environment.objects.all()
    serializer_class = serializers.EnvironmentSerializer


class ServiceViewSet(RalphAPIViewSet):
    class ServiceFilterSet(django_filters.FilterSet):
        active = BooleanFilter(field_name="active")

        class Meta:
            model = models.Service
            fields = ["active"]

    queryset = models.Service.objects.all()
    serializer_class = serializers.ServiceSerializer
    save_serializer_class = serializers.SaveServiceSerializer
    select_related = ["profit_center"]
    prefetch_related = ["business_owners", "technical_owners", "environments"]
    additional_filter_class = ServiceFilterSet


class ServiceEnvironmentViewSet(RalphAPIViewSet):
    class ServiceEnvFilterSet(django_filters.FilterSet):
        service__active = BooleanFilter(field_name="service__active")
        service__uid = Filter(field_name="service__uid", lookup_expr="iexact")
        service__id = Filter(field_name="service__id", lookup_expr="iexact")
        service__name = Filter(field_name="service__name", lookup_expr="iexact")
        environment__name = Filter(field_name="environment__name", lookup_expr="iexact")
        environment__id = Filter(field_name="environment__id", lookup_expr="iexact")

        class Meta:
            model = models.Service
            fields = ["active"]

    queryset = models.ServiceEnvironment.objects.all()
    serializer_class = serializers.ServiceEnvironmentSerializer
    select_related = ["service", "environment", "service__support_team"]
    # allow to only add environments through service resource
    http_method_names = ["get", "delete"]
    prefetch_related = ["tags"] + [
        "service__{}".format(pr) for pr in ServiceViewSet.prefetch_related
    ]
    additional_filter_class = ServiceEnvFilterSet


class ManufacturerViewSet(RalphAPIViewSet):
    queryset = models.Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer


class ManufacturerKindViewSet(RalphAPIViewSet):
    queryset = models.ManufacturerKind.objects.all()
    serializer_class = serializers.ManufacturerKindSerializer


class CategoryViewSet(RalphAPIViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer


class AssetModelViewSet(RalphAPIViewSet):
    queryset = models.AssetModel.objects.all()
    serializer_class = serializers.AssetModelSerializer
    save_serializer_class = serializers.AssetModelSaveSerializer
    select_related = ["manufacturer"]
    prefetch_related = ["custom_fields"]


class BaseObjectFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = models.BaseObject


base_object_descendant_prefetch_related = [
    Prefetch(
        "licences",
        queryset=BaseObjectLicence.objects.select_related(
            *BaseObjectLicenceViewSet.select_related
        ),
    ),
    "custom_fields",
    "service_env__service__business_owners",
    "service_env__service__technical_owners",
]


class BaseObjectDescendantViewSetMixin(RalphAPIViewSet):
    prefetch_related = base_object_descendant_prefetch_related


BASE_OBJECT_NAME_FILTER_FIELDS = [
    "asset__hostname",
    "virtualserver__hostname",
    "cloudhost__hostname",
    "cluster__hostname",
    "cluster__name",
    "configurationclass__path",
    "serviceenvironment__service__name",
    "cloudproject__name",
]


class BaseObjectViewSet(PolymorphicViewSetMixin, RalphAPIViewSet):
    queryset = models.BaseObject.polymorphic_objects.all()
    serializer_class = serializers.BaseObjectPolymorphicSerializer
    http_method_names = ["get", "options", "head"]
    filterset_fields = [
        "id",
        "service_env",
        "service_env",
        "service_env__service__uid",
        "content_type",
    ]
    extended_filter_fields = {
        "name": BASE_OBJECT_NAME_FILTER_FIELDS,
        "__str__": BASE_OBJECT_NAME_FILTER_FIELDS,
        "hostname": [
            "asset__hostname",
            "virtualserver__hostname",
            "cloudhost__hostname",
            "cluster__hostname",
        ],
        "sn": ["asset__sn"],
        "barcode": ["asset__barcode"],
        "price": ["asset__price"],
        "ip": ["ethernet_set__ipaddress__address"],
        "uid": ["serviceenvironment__service__uid"],
        "service": ["service_env__service__uid", "service_env__service__name"],
        "env": ["service_env__environment__name"],
    }
    additional_filter_class = BaseObjectFilterSet

    def get_object(self):
        return self.get_queryset().filter(pk=self.kwargs["pk"]).first()


class AssetHolderViewSet(RalphAPIViewSet):
    queryset = models.AssetHolder.objects.all()
    serializer_class = serializers.AssetHolderSerializer


class EthernetViewSet(RalphAPIViewSet):
    queryset = models.Ethernet.objects.all()
    serializer_class = serializers.EthernetSerializer
    filterset_fields = ["base_object", "ipaddress__address"]
    prefetch_related = ["base_object", "base_object__tags"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            if instance and instance.ipaddress.dhcp_expose:
                raise ValidationError(
                    "Could not delete Ethernet when it is exposed in DHCP"
                )
        except IPAddress.DoesNotExist:
            pass
        return super().destroy(request, *args, **kwargs)


class MemoryViewSet(RalphAPIViewSet):
    queryset = models.Memory.objects.all()
    serializer_class = serializers.MemorySerializer
    filterset_fields = ["base_object", "size"]
    prefetch_related = ["base_object", "base_object__tags"]


class FibreChannelCardViewSet(RalphAPIViewSet):
    queryset = models.FibreChannelCard.objects.all()
    serializer_class = serializers.FibreChannelCardSerializer
    filterset_fields = ["base_object", "wwn"]
    prefetch_related = ["base_object", "base_object__tags"]


class ProcessorViewSet(RalphAPIViewSet):
    queryset = models.Processor.objects.all()
    serializer_class = serializers.ProcessorSerializer
    filterset_fields = ["base_object", "cores"]
    prefetch_related = ["base_object", "base_object__tags"]


class DiskViewSet(RalphAPIViewSet):
    queryset = models.Disk.objects.all()
    serializer_class = serializers.DiskSerializer
    filterset_fields = ["base_object", "serial_number", "size"]
    prefetch_related = ["base_object", "base_object__tags"]


class ConfigurationModuleViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationModule.objects.all()
    serializer_class = serializers.ConfigurationModuleSerializer
    save_serializer_class = serializers.ConfigurationModuleSimpleSerializer
    filterset_fields = ("parent", "name")
    # don't allow for ConfigurationModule updating or deleting as it might
    # dissrupt configuration of many hosts!
    http_method_names = ["get", "post", "options", "head"]


class ConfigurationClassViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationClass.objects.all()
    serializer_class = serializers.ConfigurationClassSerializer
    filterset_fields = ("module", "module__name", "class_name", "path")
    select_related = ["module"]
    prefetch_related = ["tags"]
    # don't allow for ConfigurationClass updating or deleting as it might
    # dissrupt configuration of many hosts!
    http_method_names = ["get", "post", "options", "head"]


class BaseObjectViewSetMixin(object):
    """
    Base class for viewsets that inherits from BaseObject
    """

    extended_filter_fields = {
        "service": ["service_env__service__uid", "service_env__service__name"],
        "env": ["service_env__environment__name"],
    }


class DCHostFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = models.BaseObject


# TODO: move to data_center and use DCHost proxy model
class DCHostViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = BaseObject.polymorphic_objects
    serializer_class = ralph.assets.api.serializers_dchosts.DCHostSerializer
    renderer_classes = renderer_classes_without_form(RalphAPIViewSet.renderer_classes)
    http_method_names = ["get", "options", "head", "patch", "post"]
    filterset_fields = [
        "id",
        "service_env",
        "service_env__service__uid",
        "content_type",
    ]
    select_related = [
        "service_env__service",
        "service_env__environment",
        "configuration_path__module",
        "parent__cloudproject",
    ]
    prefetch_related = [
        "tags",
        "custom_fields",
        "ethernet_set__ipaddress",
    ]
    extended_filter_fields = {
        "name": [
            "asset__hostname",
            "virtualserver__hostname",
            "cloudhost__hostname",
        ],
        "hostname": [
            "asset__hostname",
            "virtualserver__hostname",
            "cloudhost__hostname",
        ],
        "ip": ["ethernet_set__ipaddress__address"],
        "service": ["service_env__service__uid", "service_env__service__name"],
        "object_type": ["content_type__model"],
        "env": ["service_env__environment__name"],
    }
    additional_filter_class = DCHostFilterSet

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method not in SAFE_METHODS:
            try:
                obj_ = self.get_object()
                if isinstance(obj_, VirtualServer):
                    from ralph.virtual.api import VirtualServerSaveSerializer

                    return VirtualServerSaveSerializer
                elif isinstance(obj_, DataCenterAsset):
                    from ralph.data_center.api.serializers import (
                        DataCenterAssetSaveSerializer,
                    )

                    return DataCenterAssetSaveSerializer
                elif isinstance(obj_, CloudHost):
                    from ralph.virtual.api import SaveCloudHostSerializer

                    return SaveCloudHostSerializer
                elif isinstance(obj_, Cluster):
                    from ralph.data_center.api.serializers import ClusterSerializer

                    return ClusterSerializer
                else:
                    raise NotFound()
            except (
                AssertionError
            ):  # for some reason when opening browsable api this raises
                pass
        return ralph.assets.api.serializers_dchosts.DCHostSerializer

    def get_queryset(self):
        return (
            self.queryset.dc_hosts()
            .filter(visibility_scope_filter(self.request.user))
            .select_related(*self.select_related)
            .polymorphic_select_related(Cluster=["type"], CloudHost=["hypervisor"])
            .polymorphic_prefetch_related(
                Cluster=[*self.prefetch_related],
                DataCenterAsset=[*self.prefetch_related],
                VirtualServer=[*self.prefetch_related],
                CloudHost=[*self.prefetch_related],
            )
        )
