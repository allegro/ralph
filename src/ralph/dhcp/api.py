# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.dhcp.models import DNSServer


class DNSServerSerializer(RalphAPISerializer):
    class Meta:
        model = DNSServer
        depth = 1


class DNSServerViewSet(RalphAPIViewSet):
    queryset = DNSServer.objects.all()
    serializer_class = DNSServerSerializer


router.register(r'dns-servers', DNSServerViewSet)
urlpatterns = []
