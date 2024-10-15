from ralph.api import RalphAPISerializer
from ralph.networks.models import IPAddress


class IPAddressSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = IPAddress
        fields = ("id", "address", "hostname", "dhcp_expose", "is_management", "url")
