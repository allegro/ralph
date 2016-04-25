# -*- coding: utf-8 -*-
from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.networks.models import IPAddress


from ralph.api import RalphAPISerializer
from ralph.assets.api.serializers import EthernetSerializer
class IPAddressSerializer(RalphAPISerializer):
    ethernet = EthernetSerializer()
    class Meta:
        model = IPAddress
        depth = 1
        exclude = (
            #'ethernet',
        )


class IPAddressViewSet(RalphAPIViewSet):
    queryset = IPAddress.objects.all()
    serializer_class = IPAddressSerializer

router.register(r'ipaddresses', IPAddressViewSet)
urlpatterns = []
