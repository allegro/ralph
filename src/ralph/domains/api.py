# -*- coding: utf-8 -*-
from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.domains.models import Domain


class DomainSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Domain
        depth = 1


class DomainViewSet(RalphAPIViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

router.register(r'domains', DomainViewSet)
urlpatterns = []
