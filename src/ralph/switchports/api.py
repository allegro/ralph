from rest_framework.fields import SerializerMethodField

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.switchports.models import Port, Connection


class PortSerializer(RalphAPISerializer):
    class Meta:
        model = Port
        fields = "__all__"


class PortViewSet(RalphAPIViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer


class ConnectionSerializer(RalphAPISerializer):
    members = SerializerMethodField()

    class Meta:
        model = Connection
        fields = "__all__"

    def get_members(self, obj):
        return [
            {
                "port_id": member.port.id,
                "port_label": member.port.label,
                "host_id": member.port.data_center_asset.id,
                "hostname": member.port.data_center_asset.hostname,
            }
            for member in obj.members.all()
        ]


class ConnectionViewSet(RalphAPIViewSet):
    queryset = Connection.objects.all().prefetch_related(
        "members__port__data_center_asset"
    )
    serializer_class = ConnectionSerializer


router.register(r"ports", PortViewSet)
router.register(r"connections", ConnectionViewSet)
urlpatterns = []
