from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.switchports.models import Port


class PortSerializer(RalphAPISerializer):
    class Meta:
        model = Port
        fields = "__all__"


class PortViewSet(RalphAPIViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer


router.register(r"ports", PortViewSet)
urlpatterns = []
