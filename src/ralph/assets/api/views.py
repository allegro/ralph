# -*- coding: utf-8 -*-
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError

from ralph.api import RalphAPIViewSet
from ralph.api.utils import PolymorphicViewSetMixin
from ralph.assets import models
from ralph.assets.api import serializers
from ralph.licences.api import BaseObjectLicenceViewSet
from ralph.licences.models import BaseObjectLicence
from ralph.networks.models import IPAddress


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
    select_related = ['service', 'environment']
    # allow to only add environments through service resource
    http_method_names = ['get', 'delete']
    prefetch_related = ['tags'] + [
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
    filter_fields = [
        'id', 'service_env', 'service_env', 'service_env__service__uid',
        'content_type'
    ]
    extended_filter_fields = {
        'name': ['asset__hostname'],
        'sn': ['asset__sn'],
        'barcode': ['asset__barcode'],
        'price': ['asset__price'],
        'ip': ['ethernet__ipaddress__address'],
        'service': ['service_env__service__uid', 'service_env__service__name'],
    }


class AssetHolderViewSet(RalphAPIViewSet):
    queryset = models.AssetHolder.objects.all()
    serializer_class = serializers.AssetHolderSerializer


class EthernetViewSet(RalphAPIViewSet):
    queryset = models.Ethernet.objects.all()
    serializer_class = serializers.EthernetSerializer
    filter_fields = ['base_object']
    prefetch_related = ['model', 'base_object', 'base_object__tags']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            if instance and instance.ipaddress.dhcp_expose:
                raise ValidationError(
                    'Could not delete Ethernet when it is exposed in DHCP'
                )
        except IPAddress.DoesNotExist:
            pass
        return super().destroy(request, *args, **kwargs)


class ConfigurationModuleViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationModule.objects.all()
    serializer_class = serializers.ConfigurationModuleSerializer
    save_serializer_class = serializers.ConfigurationModuleSimpleSerializer
    filter_fields = ('parent', 'name')


class ConfigurationClassViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationClass.objects.all()
    serializer_class = serializers.ConfigurationClassSerializer
    filter_fields = ('module', 'module__name', 'class_name', 'path')


class BaseObjectViewSetMixin(object):
    """
    Base class for viewsets that inherits from BaseObject
    """
    extended_filter_fields = {
        'service': ['service_env__service__uid', 'service_env__service__name']
    }
