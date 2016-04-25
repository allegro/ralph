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
    prefetch_related = [
        'ethernet', 'ethernet__base_object', 'ethernet__base_object__tags',
        'network',
    ]

router.register(r'ipaddresses', IPAddressViewSet)
urlpatterns = []
