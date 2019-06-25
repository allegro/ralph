# -*- coding: utf-8 -*-
from django.db import transaction
from django.db.models import Prefetch
from rest_framework import relations, serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.api.filters import NetworkableObjectFilters
from ralph.assets.api.serializers import (
    BaseObjectSerializer,
    ComponentSerializerMixin,
    NetworkComponentSerializerMixin,
    ServiceEnvironmentSimpleSerializer
)
from ralph.assets.api.views import (
    base_object_descendant_prefetch_related,
    BaseObjectViewSetMixin
)
from ralph.assets.models import Ethernet
from ralph.configuration_management.api import SCMInfoSerializer
from ralph.data_center.api.serializers import DataCenterAssetSimpleSerializer
from ralph.data_center.models import DCHost
from ralph.security.api import SecurityScanSerializer
from ralph.security.models import SecurityScan
from ralph.virtual.admin import VirtualServerAdmin
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudImage,
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
    _validate_using_model_clean = False
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
    _validate_using_model_clean = False
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


class CloudHostSerializer(
    NetworkComponentSerializerMixin, BaseObjectSerializer
):
    hypervisor = DataCenterAssetSimpleSerializer()
    parent = CloudProjectSimpleSerializer(source='cloudproject')
    cloudflavor = CloudFlavorSimpleSerializer()
    service_env = ServiceEnvironmentSimpleSerializer()
    scmstatuscheck = SCMInfoSerializer()
    securityscan = SecurityScanSerializer()

    class Meta(BaseObjectSerializer.Meta):
        model = CloudHost
        depth = 1


class CloudProjectSerializer(BaseObjectSerializer):
    cloud_hosts = CloudHostSimpleSerializer(many=True, source='children')

    class Meta(BaseObjectSerializer.Meta):
        model = CloudProject
        depth = 2
        exclude = ['content_type', 'parent']


class CloudImageSerializer(RalphAPISerializer):
    class Meta:
        model = CloudImage


class CloudProviderSerializer(RalphAPISerializer):
    class Meta:
        model = CloudProvider


class VirtualServerTypeSerializer(RalphAPISerializer):
    class Meta:
        model = VirtualServerType


class VirtualServerSimpleSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer):
        model = VirtualServer
        fields = ['hostname', 'url']
        _skip_tags_field = True


# TODO: select related
class VirtualServerSerializer(ComponentSerializerMixin, BaseObjectSerializer):
    type = VirtualServerTypeSerializer()
    # TODO: cast BaseObject to DataCenterAsset for hypervisor field
    hypervisor = DataCenterAssetSimpleSerializer(source='parent')
    # TODO: clusters
    scmstatuscheck = SCMInfoSerializer()
    securityscan = SecurityScanSerializer()

    class Meta(BaseObjectSerializer.Meta):
        model = VirtualServer
        exclude = ('content_type', 'cluster')


class VirtualServerSaveSerializer(RalphAPISaveSerializer):
    hypervisor = relations.PrimaryKeyRelatedField(
        source='parent', queryset=DCHost.objects,
    )

    class Meta:
        model = VirtualServer
        exclude = ('parent',)


class CloudFlavorViewSet(RalphAPIViewSet):
    queryset = CloudFlavor.objects.all()
    serializer_class = CloudFlavorSerializer
    save_serializer_class = SaveCloudFlavorSerializer
    prefetch_related = ['tags', 'virtualcomponent_set__model']
    filter_fields = ['flavor_id']


class CloudProviderViewSet(RalphAPIViewSet):
    queryset = CloudProvider.objects.all()
    serializer_class = CloudProviderSerializer


class CloudImageViewSet(RalphAPIViewSet):
    queryset = CloudImage.objects.all()
    serializer_class = CloudImageSerializer
    filter_fields = ['image_id']


class CloudHostViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = CloudHost.objects.all()
    serializer_class = CloudHostSerializer
    save_serializer_class = SaveCloudHostSerializer
    select_related = [
        'parent', 'parent__cloudproject', 'cloudprovider', 'hypervisor',
        'service_env__service', 'service_env__environment', 'content_type',
        'configuration_path__module',
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        'tags', 'cloudflavor__virtualcomponent_set__model', 'licences',
        Prefetch(
            'ethernet_set',
            queryset=Ethernet.objects.select_related('ipaddress')
        ),
        Prefetch(
            'securityscan',
            queryset=SecurityScan.objects.prefetch_related(
                'vulnerabilities', 'tags'
            )
        ),
    ]


class CloudProjectViewSet(RalphAPIViewSet):
    queryset = CloudProject.objects.all()
    serializer_class = CloudProjectSerializer
    prefetch_related = [
        'children', 'tags', 'licences', 'cloudprovider',
    ]


class VirtualServerTypeViewSet(RalphAPIViewSet):
    queryset = VirtualServerType.objects.all()
    serializer_class = VirtualServerTypeSerializer
    filter_fields = ['name']


class VirtualServerFilterSet(NetworkableObjectFilters):
    class Meta(NetworkableObjectFilters.Meta):
        model = VirtualServer


class VirtualServerViewSet(BaseObjectViewSetMixin, RalphAPIViewSet):
    queryset = VirtualServer.objects.all()
    serializer_class = VirtualServerSerializer
    save_serializer_class = VirtualServerSaveSerializer
    select_related = VirtualServerAdmin.list_select_related + [
        'parent', 'service_env__service', 'service_env__environment',
        'configuration_path', 'content_type'
    ]
    prefetch_related = base_object_descendant_prefetch_related + [
        'tags',
        'memory_set',
        'processor_set',
        'disk_set',
        Prefetch(
            'ethernet_set',
            queryset=Ethernet.objects.select_related('ipaddress')
        ),
        Prefetch(
            'securityscan',
            queryset=SecurityScan.objects.prefetch_related(
                'vulnerabilities', 'tags'
            )
        ),
        # TODO: clusters
    ]
    filter_fields = [
        'service_env__service__uid',
        'service_env__service__name',
        'service_env__service__id',
    ]
    additional_filter_class = VirtualServerFilterSet
    extended_filter_fields = dict(
        list(BaseObjectViewSetMixin.extended_filter_fields.items()) +
        list(dict(
            hypervisor_service=['parent__service_env__service__uid'],
        ).items())
    )


router.register(r'cloud-flavors', CloudFlavorViewSet)
router.register(r'cloud-hosts', CloudHostViewSet)
router.register(r'cloud-projects', CloudProjectViewSet)
router.register(r'cloud-providers', CloudProviderViewSet)
router.register(r'cloud-images', CloudImageViewSet)
router.register(r'virtual-servers', VirtualServerViewSet)
router.register(r'virtual-server-types', VirtualServerTypeViewSet)
urlpatterns = []
