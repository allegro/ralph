# -*- coding: utf-8 -*-
import django_filters
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError

from ralph.api import RalphAPIViewSet
from ralph.api.filters import BooleanFilter
from ralph.api.utils import PolymorphicViewSetMixin
from ralph.assets import models
from ralph.assets.api import serializers
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.lib.custom_fields.models import CustomFieldValue
from ralph.licences.api import BaseObjectLicenceViewSet
from ralph.licences.models import BaseObjectLicence
from ralph.networks.models import IPAddress


class BusinessSegmentViewSet(RalphAPIViewSet):
    queryset = models.BusinessSegment.objects.all()
    serializer_class = serializers.BusinessSegmentSerializer


class ProfitCenterViewSet(RalphAPIViewSet):
    queryset = models.ProfitCenter.objects.all()
    serializer_class = serializers.ProfitCenterSerializer
    prefetch_related = ['business_segment']


class BudgetInfoViewSet(RalphAPIViewSet):
    queryset = models.BudgetInfo.objects.all()
    serializer_class = serializers.BudgetInfoSerializer


class EnvironmentViewSet(RalphAPIViewSet):
    queryset = models.Environment.objects.all()
    serializer_class = serializers.EnvironmentSerializer


class ServiceFilterSet(django_filters.FilterSet):
    active = BooleanFilter(name='active')

    class Meta:
        model = models.Service
        fields = ['active']


class ServiceViewSet(RalphAPIViewSet):
    queryset = models.Service.objects.all()
    serializer_class = serializers.ServiceSerializer
    save_serializer_class = serializers.SaveServiceSerializer
    select_related = ['profit_center']
    prefetch_related = ['business_owners', 'technical_owners', 'environments']
    additional_filter_class = ServiceFilterSet


class ServiceEnvironmentViewSet(RalphAPIViewSet):
    queryset = models.ServiceEnvironment.objects.all()
    serializer_class = serializers.ServiceEnvironmentSerializer
    select_related = ['service', 'environment', 'service__support_team']
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
    save_serializer_class = serializers.AssetModelSaveSerializer
    select_related = ['manufacturer']


class BaseObjectFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = models.BaseObject


base_object_descendant_prefetch_related = [
    Prefetch('licences', queryset=BaseObjectLicence.objects.select_related(
        *BaseObjectLicenceViewSet.select_related
    )),
    Prefetch(
        'custom_fields',
        queryset=CustomFieldValue.objects.select_related('custom_field')
    ),
    'service_env__service__business_owners',
    'service_env__service__technical_owners',
]


class BaseObjectDescendantViewSetMixin(RalphAPIViewSet):
    prefetch_related = base_object_descendant_prefetch_related

BASE_OBJECT_NAME_FILTER_FIELDS = [
    'asset__hostname',
    'virtualserver__hostname',
    'cloudhost__hostname',
    'cluster__hostname',
    'configurationclass__path',
    'serviceenvironment__service__name',
    'cloudproject__name',
]


class BaseObjectViewSet(PolymorphicViewSetMixin, RalphAPIViewSet):
    queryset = models.BaseObject.polymorphic_objects.all()
    serializer_class = serializers.BaseObjectPolymorphicSerializer
    http_method_names = ['get', 'options', 'head']
    filter_fields = [
        'id', 'service_env', 'service_env', 'service_env__service__uid',
        'content_type'
    ]
    extended_filter_fields = {
        'name': BASE_OBJECT_NAME_FILTER_FIELDS,
        '__str__': BASE_OBJECT_NAME_FILTER_FIELDS,
        'hostname': [
            'asset__hostname',
            'virtualserver__hostname',
            'cloudhost__hostname',
            'cluster__hostname',
        ],
        'sn': ['asset__sn'],
        'barcode': ['asset__barcode'],
        'price': ['asset__price'],
        'ip': ['ethernet_set__ipaddress__address'],
        'service': ['service_env__service__uid', 'service_env__service__name'],
        'env': ['service_env__environment__name'],
    }
    additional_filter_class = BaseObjectFilterSet


class AssetHolderViewSet(RalphAPIViewSet):
    queryset = models.AssetHolder.objects.all()
    serializer_class = serializers.AssetHolderSerializer


class EthernetViewSet(RalphAPIViewSet):
    queryset = models.Ethernet.objects.all()
    serializer_class = serializers.EthernetSerializer
    filter_fields = ['base_object', 'ipaddress__address']
    prefetch_related = ['base_object', 'base_object__tags']

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


class MemoryViewSet(RalphAPIViewSet):
    queryset = models.Memory.objects.all()
    serializer_class = serializers.MemorySerializer
    filter_fields = ['base_object', 'size']
    prefetch_related = ['base_object', 'base_object__tags']


class FibreChannelCardViewSet(RalphAPIViewSet):
    queryset = models.FibreChannelCard.objects.all()
    serializer_class = serializers.FibreChannelCardSerializer
    filter_fields = ['base_object', 'wwn']
    prefetch_related = ['base_object', 'base_object__tags']


class ProcessorViewSet(RalphAPIViewSet):
    queryset = models.Processor.objects.all()
    serializer_class = serializers.ProcessorSerializer
    filter_fields = ['base_object', 'cores']
    prefetch_related = ['base_object', 'base_object__tags']


class DiskViewSet(RalphAPIViewSet):
    queryset = models.Disk.objects.all()
    serializer_class = serializers.DiskSerializer
    filter_fields = ['base_object', 'serial_number', 'size']
    prefetch_related = ['base_object', 'base_object__tags']


class ConfigurationModuleViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationModule.objects.all()
    serializer_class = serializers.ConfigurationModuleSerializer
    save_serializer_class = serializers.ConfigurationModuleSimpleSerializer
    filter_fields = ('parent', 'name')


class ConfigurationClassViewSet(RalphAPIViewSet):
    queryset = models.ConfigurationClass.objects.all()
    serializer_class = serializers.ConfigurationClassSerializer
    filter_fields = ('module', 'module__name', 'class_name', 'path')
    select_related = ['module']
    prefetch_related = ['tags']


class BaseObjectViewSetMixin(object):
    """
    Base class for viewsets that inherits from BaseObject
    """
    extended_filter_fields = {
        'service': ['service_env__service__uid', 'service_env__service__name'],
        'env': ['service_env__environment__name'],
    }


class DCHostFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = models.BaseObject


# TODO: move to data_center and use DCHost proxy model
class DCHostViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = models.BaseObject.polymorphic_objects
    serializer_class = serializers.DCHostSerializer
    http_method_names = ['get', 'options', 'head']
    filter_fields = [
        'id', 'service_env', 'service_env__service__uid',
        'content_type',
    ]
    select_related = [
        'service_env', 'service_env__service', 'service_env__environment',
        'configuration_path', 'configuration_path__module'
    ]
    prefetch_related = [
        'tags',
        Prefetch(
            'ethernet_set',
            queryset=models.Ethernet.objects.select_related('ipaddress')
        ),
        Prefetch(
            'custom_fields',
            queryset=CustomFieldValue.objects.select_related('custom_field')
        ),
    ]
    extended_filter_fields = {
        'name': [
            'asset__hostname',
            'virtualserver__hostname',
            'cloudhost__hostname',
        ],
        'hostname': [
            'asset__hostname',
            'virtualserver__hostname',
            'cloudhost__hostname',
        ],
        'ip': ['ethernet_set__ipaddress__address'],
        'service': ['service_env__service__uid', 'service_env__service__name'],
        'object_type': ['content_type__model'],
        'env': ['service_env__environment__name'],
    }
    additional_filter_class = DCHostFilterSet

    def get_queryset(self):
        return super().get_queryset().dc_hosts()
