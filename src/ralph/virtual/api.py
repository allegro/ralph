# -*- coding: utf-8 -*-
from django.db import transaction
from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.api.serializers import (
    BaseObjectSerializer,
    BaseObjectPolymorphicSerializer,
    ServiceEnvironmentSimpleSerializer
)
from ralph.data_center.api.serializers import DataCenterAssetSimpleSerializer
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualServer,
    VirtualServerType
)


class CloudFlavorSimpleSerializer(BaseObjectSerializer):
    class Meta:
        model = CloudFlavor
        fields = ['name', 'cores', 'memory', 'disk', 'url']
        _skip_tags_field = True


class CloudHostSimpleSerializer(BaseObjectSerializer):
    ip_addresses = serializers.ListField()

    class Meta:
        model = CloudHost
        fields = ['hostname', 'ip_addresses', 'url']


class CloudProjectSimpleSerializer(BaseObjectSerializer):
    class Meta:
        model = CloudProject
        fields = ['name', 'url', 'project_id']
        _skip_tags_field = True


class SaveCloudFlavorSerializer(RalphAPISaveSerializer):
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


class SaveCloudHostSerializer(RalphAPISaveSerializer):
    ip_addresses = serializers.ListField()

    def create(self, validated_data):
        ip_addresses = validated_data.pop('ip_addresses')
        instance = super().create(validated_data)
        instance.ip_addresses = ip_addresses
        return instance

    class Meta:
        model = CloudHost
        exclude = ['content_type']


class CloudFlavorSerializer(BaseObjectSerializer):
    cores = serializers.IntegerField()
    memory = serializers.IntegerField()
    disk = serializers.IntegerField()

    class Meta(BaseObjectSerializer.Meta):
        model = CloudFlavor
        exclude = ['content_type', 'service_env', 'parent']


class CloudHostSerializer(BaseObjectSerializer):
    ip_addresses = serializers.ListField()
    hypervisor = DataCenterAssetSimpleSerializer()
    parent = CloudProjectSimpleSerializer(source='cloudproject')
    cloudflavor = CloudFlavorSimpleSerializer()
    service_env = ServiceEnvironmentSimpleSerializer()

    class Meta(BaseObjectSerializer.Meta):
        model = CloudHost
        depth = 1


class CloudProjectSerializer(BaseObjectSerializer):
    cloud_hosts = CloudHostSimpleSerializer(many=True, source='children')

    class Meta(BaseObjectSerializer.Meta):
        model = CloudProject
        depth = 2
        exclude = ['content_type', 'parent']


class CloudProviderSerializer(RalphAPISerializer):
    class Meta:
        model = CloudProvider


class VirtualServerTypeSerializer(RalphAPISerializer):
    class Meta:
        model = VirtualServerType


class VirtualServerSerializer(BaseObjectSerializer):
    type = VirtualServerTypeSerializer()
    parent = BaseObjectPolymorphicSerializer()

    class Meta(BaseObjectSerializer.Meta):
        model = VirtualServer


class CloudFlavorViewSet(RalphAPIViewSet):
    queryset = CloudFlavor.objects.all()
    serializer_class = CloudFlavorSerializer
    save_serializer_class = SaveCloudFlavorSerializer
    prefetch_related = ['tags', 'virtualcomponent__model']


class CloudProviderViewSet(RalphAPIViewSet):
    queryset = CloudProvider.objects.all()
    serializer_class = CloudProviderSerializer


class CloudHostViewSet(RalphAPIViewSet):
    queryset = CloudHost.objects.all()
    serializer_class = CloudHostSerializer
    save_serializer_class = SaveCloudHostSerializer
    select_related = ['parent', 'service_env__service',
                      'service_env__environment', 'hypervisor']
    prefetch_related = [
        'tags', 'cloudflavor__virtualcomponent__model'
    ]


class CloudProjectViewSet(RalphAPIViewSet):
    queryset = CloudProject.objects.all()
    serializer_class = CloudProjectSerializer
    prefetch_related = [
        'children', 'tags', 'licences',
    ]


class VirtualServerTypeViewSet(RalphAPIViewSet):
    queryset = VirtualServerType.objects.all()
    serializer_class = VirtualServerTypeSerializer


class VirtualServerViewSet(RalphAPIViewSet):
    queryset = VirtualServer.objects.all()
    serializer_class = VirtualServerSerializer


router.register(r'cloud-flavors', CloudFlavorViewSet)
router.register(r'cloud-hosts', CloudHostViewSet)
router.register(r'cloud-projects', CloudProjectViewSet)
router.register(r'cloud-providers', CloudProviderViewSet)
router.register(r'virtual-servers', VirtualServerViewSet)
router.register(r'virtual-server-types', VirtualServerTypeViewSet)
urlpatterns = []
