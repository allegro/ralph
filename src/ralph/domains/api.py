# -*- coding: utf-8 -*-
from ralph.accounts.api import RalphUserSimpleSerializer
from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.domains.models import Domain


class DomainSerializer(BaseObjectSerializer):
    business_owner = RalphUserSimpleSerializer()
    technical_owner = RalphUserSimpleSerializer()

    class Meta(BaseObjectSerializer.Meta):
        model = Domain
        depth = 1


class DomainViewSet(RalphAPIViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    select_related = [
        'service_env__service', 'service_env__environment', 'business_segment',
        'business_owner', 'technical_owner', 'domain_holder'
    ]
    prefetch_related = ['tags']

router.register(r'domains', DomainViewSet)
urlpatterns = []
