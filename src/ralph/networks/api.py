# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import EthernetSerializer
from ralph.networks.models import (
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)


class NetworkEnvironmentSerializer(RalphAPISerializer):
    class Meta:
        model = NetworkEnvironment
        depth = 1


class NetworkKindSerializer(RalphAPISerializer):
    class Meta:
        model = NetworkKind
        depth = 1


class NetworkSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Network
        fields = (
            'id', 'url', 'name', 'remarks', 'vlan', 'dhcp_broadcast', 'parent',
            'network_environment'
        )


class NetworkSerializer(RalphAPISerializer):
    class Meta:
        model = Network
        depth = 1


class IPAddressSerializer(RalphAPISerializer):
    ethernet = EthernetSerializer()
    network = NetworkSimpleSerializer()

    class Meta:
        model = IPAddress
        depth = 1
        exclude = (
            # 'ethernet',
        )


class IPAddressViewSet(RalphAPIViewSet):
    queryset = IPAddress.objects.all()
    serializer_class = IPAddressSerializer
    prefetch_related = [
        'ethernet', 'ethernet__base_object', 'ethernet__base_object__tags',
        'network',
    ]


class NetworkViewSet(RalphAPIViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    select_related = ['network_environment', 'kind']
    prefetch_related = ['racks', 'dns_servers']


class NetworkEnvironmentViewSet(RalphAPIViewSet):
    queryset = NetworkEnvironment.objects.all()
    serializer_class = NetworkEnvironmentSerializer


class NetworkKindViewSet(RalphAPIViewSet):
    queryset = NetworkKind.objects.all()
    serializer_class = NetworkKindSerializer

router.register(r'ipaddresses', IPAddressViewSet)
router.register(r'networks', NetworkViewSet)
router.register(r'network-environments', NetworkEnvironmentViewSet)
router.register(r'network-kinds', NetworkKindViewSet)
urlpatterns = []
