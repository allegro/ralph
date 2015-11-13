# -*- coding: utf-8 -*-
from django.db import transaction
from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.data_center.api.serializers import DataCenterAssetSimpleSerializer
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider
)


class CloudFlavorSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = CloudFlavor
        fields = ['name', 'tags', 'cores', 'memory', 'disk', 'url']


class CloudHostSimpleSerializer(BaseObjectSerializer):
    ip_addresses = serializers.ListField()

    class Meta:
        model = CloudHost
        fields = ['hostname', 'ip_addresses', 'url']


class CloudProjectSimpleSerializer(BaseObjectSerializer):
    class Meta:
        model = CloudProject
        fields = ['name', 'tags', 'url']


class SaveCloudFlavorSerializer(RalphAPISerializer):
    cores = serializers.IntegerField()
    memory = serializers.IntegerField()
    disk = serializers.IntegerField()

    @transaction.atomic
    def create(self, validated_data):
        cores = validated_data.pop('cores')
        memory = validated_data.pop('memory')
        disk = validated_data.pop('disk')
        instance = super().create(validated_data)
        instance.cores = cores
        instance.memory = memory
        instance.disk = disk
        return instance

    class Meta:
        model = CloudFlavor
        exclude = ['content_type']


class SaveCloudHostSerializer(RalphAPISerializer):
    ip_addresses = serializers.ListField()

    def create(self, validated_data):
        ip_addresses = validated_data.pop('ip_addresses')
        instance = super().create(validated_data)
        instance.ip_addresses = ip_addresses
        return instance

    class Meta:
        model = CloudHost
        exclude = ['content_type']


class CloudFlavorSerializer(RalphAPISerializer):
    cores = serializers.IntegerField()
    memory = serializers.IntegerField()
    disk = serializers.IntegerField()

    class Meta:
        model = CloudFlavor
        exclude = ['content_type', 'service_env', 'parent']


class CloudHostSerializer(RalphAPISerializer):
    ip_addresses = serializers.ListField()
    hypervisor = DataCenterAssetSimpleSerializer()
    parent = CloudProjectSimpleSerializer(source='cloudproject')
    cloudflavor = CloudFlavorSimpleSerializer()

    class Meta:
        model = CloudHost
        depth = 1
        exclude = ['content_type']


class CloudProjectSerializer(BaseObjectSerializer):
    cloud_hosts = CloudHostSimpleSerializer(many=True, source='children')

    class Meta:
        model = CloudProject
        depth = 2
        exclude = ['content_type', 'parent']


class CloudProviderSerializer(RalphAPISerializer):
    class Meta:
        model = CloudProvider


class CloudFlavorViewSet(RalphAPIViewSet):
    queryset = CloudFlavor.objects.all()
    serializer_class = CloudFlavorSerializer
    save_serializer_class = SaveCloudFlavorSerializer
    prefetch_related = ['tags']


class CloudProviderViewSet(RalphAPIViewSet):
    queryset = CloudProvider.objects.all()
    serializer_class = CloudProviderSerializer


class CloudHostViewSet(RalphAPIViewSet):
    queryset = CloudHost.objects.all()
    serializer_class = CloudHostSerializer
    save_serializer_class = SaveCloudHostSerializer
    select_related = ['parent', 'service_env__service',
                      'service_env__environment']


class CloudProjectViewSet(RalphAPIViewSet):
    queryset = CloudProject.objects.all()
    serializer_class = CloudProjectSerializer


router.register(r'cloud-flavors', CloudFlavorViewSet)
router.register(r'cloud-hosts', CloudHostViewSet)
router.register(r'cloud-projects', CloudProjectViewSet)
router.register(r'cloud-providers', CloudProviderViewSet)
urlpatterns = []
