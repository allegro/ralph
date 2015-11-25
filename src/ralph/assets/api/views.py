# -*- coding: utf-8 -*-
from django.db.models import Prefetch

from ralph.api import RalphAPIViewSet
from ralph.api.utils import PolymorphicViewSetMixin
from ralph.assets import models
from ralph.assets.api import serializers
from ralph.licences.api import BaseObjectLicenceViewSet
from ralph.licences.models import BaseObjectLicence


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
    filter_fields = ['id']
    extend_filter_fields = {
        'name': ['asset__hostname'],
        'sn': ['asset__sn'],
        'barcode': ['asset__barcode'],
    }


class AssetHolderViewSet(RalphAPIViewSet):
    queryset = models.AssetHolder.objects.all()
    serializer_class = serializers.AssetHolderSerializer
