# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.dhcp.models import DNSServer, DNSServerGroup


class DNSServerGroupSerializer(RalphAPISerializer):
    class Meta:
        model = DNSServerGroup
        fields = "__all__"


class DNSServerSerializer(RalphAPISerializer):
    class Meta:
        model = DNSServer
        depth = 1
        fields = "__all__"


class DNSServerViewSet(RalphAPIViewSet):
    queryset = DNSServer.objects.all()
    serializer_class = DNSServerSerializer


class DNSServerGroupViewSet(RalphAPIViewSet):
    queryset = DNSServerGroup.objects.all()
    serializer_class = DNSServerGroupSerializer


router.register(r"dns-servers", DNSServerViewSet)
router.register(r"dns-server-group", DNSServerGroupViewSet)
urlpatterns = []
