# -*- coding: utf-8 -*-
from django.db.models import Prefetch

from ralph.api import RalphAPIViewSet
from ralph.api.utils import PolymorphicViewSetMixin
from ralph.assets import models
from ralph.assets.api import serializers
from ralph.assets.models import components
from ralph.licences.api import BaseObjectLicenceViewSet
from ralph.licences.models import BaseObjectLicence


class DiskShareComponentViewSet(RalphAPIViewSet):
    queryset = components.DiskShareComponent.objects.all()
    serializer_class = serializers.DiskShareComponentSerializer


class DiskShareMountComponentViewSet(RalphAPIViewSet):
    queryset = components.DiskShareMountComponent.objects.all()
    serializer_class = serializers.DiskShareMountComponentSerializer
    select_related = ['share']


class ProcessorComponentViewSet(RalphAPIViewSet):
    queryset = components.ProcessorComponent.objects.all()
    serializer_class = serializers.ProcessorComponentSerializer


class MemoryComponentViewSet(RalphAPIViewSet):
    queryset = components.MemoryComponent.objects.all()
    serializer_class = serializers.MemoryComponentSerializer


class FibreChannelComponentViewSet(RalphAPIViewSet):
    queryset = components.FibreChannelComponent.objects.all()
    serializer_class = serializers.FibreChannelComponentSerializer


class SoftwareComponentViewSet(RalphAPIViewSet):
    queryset = components.SoftwareComponent.objects.all()
    serializer_class = serializers.SoftwareComponentSerializer


class OperatingSystemComponentViewSet(RalphAPIViewSet):
    queryset = components.OperatingSystemComponent.objects.all()
    serializer_class = serializers.OperatingSystemComponentSerializer


class ComponentModelViewset(RalphAPIViewSet):
    queryset = components.ComponentModel.objects.all()
    serializer_class = serializers.ComponentModelSerializer


class GenericComponentViewset(RalphAPIViewSet):
    queryset = components.GenericComponent.objects.all()
    serializer_class = serializers.GenericComponentSerializer
    select_related = ['base_object', 'model']
    prefetch_related = ['base_object__tags']
    filter_fields = ['id', 'sn', 'label']


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
    queryset = models.Service.objects.all()
    serializer_class = serializers.ServiceSerializer
    save_serializer_class = serializers.SaveServiceSerializer
    select_related = ['profit_center']
    prefetch_related = ['business_owners', 'technical_owners', 'environments']


class ServiceEnvironmentViewSet(RalphAPIViewSet):
    queryset = models.ServiceEnvironment.objects.all()
    serializer_class = serializers.ServiceEnvironmentSerializer
    # allow to only add environments through service resource
    http_method_names = ['get', 'delete']
    prefetch_related = [
        'service__{}'.format(pr) for pr in ServiceViewSet.prefetch_related
    ]
    filter_fields = [
        'service__uid', 'service__name', 'service__id',
        'environment__name', 'environment__id',
    ]


class ManufacturerViewSet(RalphAPIViewSet):
    queryset = models.Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer


class CategoryViewSet(RalphAPIViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer


class AssetModelViewSet(RalphAPIViewSet):
    queryset = models.AssetModel.objects.all()
    serializer_class = serializers.AssetModelSerializer


class BaseObjectViewSet(PolymorphicViewSetMixin, RalphAPIViewSet):
    queryset = models.BaseObject.polymorphic_objects.all()
    serializer_class = serializers.BaseObjectPolymorphicSerializer
    http_method_names = ['get', 'options', 'head']
    prefetch_related = [
        Prefetch('licences', queryset=BaseObjectLicence.objects.select_related(
            *BaseObjectLicenceViewSet.select_related
        )),
    ]
    filter_fields = ['id', 'service_env', 'service_env__service__uid']
    extended_filter_fields = {
        'name': ['asset__hostname'],
        'sn': ['asset__sn'],
        'barcode': ['asset__barcode'],
    }


class AssetHolderViewSet(RalphAPIViewSet):
    queryset = models.AssetHolder.objects.all()
    serializer_class = serializers.AssetHolderSerializer
