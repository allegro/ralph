# -*- coding: utf-8 -*-
from django.conf import settings
from rest_framework.exceptions import ValidationError

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
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
        fields = "__all__"


class NetworkKindSerializer(RalphAPISerializer):
    class Meta:
        model = NetworkKind
        depth = 1
        fields = "__all__"


class NetworkSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Network
        fields = (
            "id",
            "url",
            "name",
            "remarks",
            "vlan",
            "dhcp_broadcast",
            "parent",
            "network_environment",
        )


class NetworkSaveSerializer(RalphAPISerializer):
    class Meta:
        model = Network
        depth = 1
        exclude = ("min_ip", "max_ip")


class NetworkSerializer(RalphAPISerializer):
    class Meta:
        model = Network
        depth = 1
        fields = "__all__"


class IPAddressSerializer(RalphAPISerializer):
    network = NetworkSimpleSerializer()
    ethernet = EthernetSerializer()

    class Meta:
        model = IPAddress
        depth = 1
        exclude = ("number",)


class IPAddressSaveSerializer(RalphAPISaveSerializer):
    class Meta:
        model = IPAddress
        fields = "__all__"

    def validate_dhcp_expose(self, value):
        """
        Check if dhcp_expose value has changed from True to False.
        """
        if (
            settings.DHCP_ENTRY_FORBID_CHANGE
            and self.instance
            and self.instance.dhcp_expose
            and not value
        ):
            raise ValidationError(
                "Cannot remove entry from DHCP. Use transition to do this."
            )
        return value


class IPAddressViewSet(RalphAPIViewSet):
    queryset = IPAddress.objects.all()
    serializer_class = IPAddressSerializer
    save_serializer_class = IPAddressSaveSerializer
    prefetch_related = [
        "ethernet",
        "ethernet__base_object",
        "ethernet__base_object__tags",
        "network",
    ]
    filter_fields = [
        "hostname",
        "ethernet__base_object",
        "network",
        "network__address",
        "status",
        "is_public",
        "is_management",
        "dhcp_expose",
        "ethernet__mac",
    ]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance and instance.dhcp_expose:
            raise ValidationError(
                "Could not delete IPAddress when it is exposed in DHCP"
            )
        return super().destroy(request, *args, **kwargs)


class NetworkViewSet(RalphAPIViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    save_serializer_class = NetworkSaveSerializer
    select_related = ["network_environment", "kind"]
    prefetch_related = ["racks__accessories", "terminators"]
    extended_filter_fields = {
        # workaround for custom field for address field defined in admin
        "address": ["address"],
    }


class NetworkEnvironmentViewSet(RalphAPIViewSet):
    queryset = NetworkEnvironment.objects.all()
    serializer_class = NetworkEnvironmentSerializer


class NetworkKindViewSet(RalphAPIViewSet):
    queryset = NetworkKind.objects.all()
    serializer_class = NetworkKindSerializer


router.register(r"ipaddresses", IPAddressViewSet)
router.register(r"networks", NetworkViewSet)
router.register(r"network-environments", NetworkEnvironmentViewSet)
router.register(r"network-kinds", NetworkKindViewSet)
urlpatterns = []
