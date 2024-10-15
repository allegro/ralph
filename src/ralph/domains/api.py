# -*- coding: utf-8 -*-
from ralph.accounts.api import RalphUserSimpleSerializer
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.domains.models import DNSProvider, Domain, DomainCategory
from ralph.domains.models.domains import DomainProviderAdditionalServices


class DomainProviderAdditionalServicesSerializer(RalphAPISerializer):
    class Meta:
        model = DomainProviderAdditionalServices
        fields = "__all__"


class DomainProviderAdditionalServicesViewSet(RalphAPIViewSet):
    queryset = DomainProviderAdditionalServices.objects.all()
    serializer_class = DomainProviderAdditionalServicesSerializer


class DomainSerializer(BaseObjectSerializer):
    business_owner = RalphUserSimpleSerializer()
    technical_owner = RalphUserSimpleSerializer()
    additional_services = DomainProviderAdditionalServicesSerializer(many=True)

    class Meta(BaseObjectSerializer.Meta):
        model = Domain
        depth = 1


class DomainViewSet(RalphAPIViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    select_related = [
        "service_env__service",
        "service_env__environment",
        "business_segment",
        "business_owner",
        "technical_owner",
        "domain_holder",
    ]
    prefetch_related = [
        "tags",
        "custom_fields",
        "content_type",
        "additional_services",
        "licences__baseobjectlicence_set",
    ]


class DNSProviderSerializer(RalphAPISerializer):
    class Meta:
        model = DNSProvider
        fields = "__all__"


class DNSProviderViewSet(RalphAPIViewSet):
    queryset = DNSProvider.objects.all()
    serializer_class = DNSProviderSerializer


class DomainCategorySerializer(RalphAPISerializer):
    class Meta:
        model = DomainCategory
        fields = "__all__"


class DomainCategoryViewSet(RalphAPIViewSet):
    queryset = DomainCategory.objects.all()
    serializer_class = DomainCategorySerializer


router.register(r"domains", DomainViewSet)
router.register(
    r"domain-provider-additional-services", DomainProviderAdditionalServicesViewSet
)
router.register(r"dns-provider", DNSProviderViewSet)
router.register(r"domain-category", DomainCategoryViewSet)
urlpatterns = []
