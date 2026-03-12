# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.domains.models import (
    DNSProvider,
    Domain,
    DomainCategory,
    DomainContract,
    DomainRegistrant,
    DomainStatus,
)
from ralph.domains.models.domains import DomainProviderAdditionalServices


class DNSProviderFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"dns-provider{n}")

    class Meta:
        model = DNSProvider


class DomainCategoryFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"domain-contract{n}")

    class Meta:
        model = DomainCategory


class DomainRegistrantFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"fancy-domain{n}.pl")

    class Meta:
        model = DomainRegistrant
        django_get_or_create = ["name"]


class DomainProviderAdditionalServicesFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"important-domain-provider{n}")

    class Meta:
        model = DomainProviderAdditionalServices
        django_get_or_create = ["name"]


class DomainFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"www.domain{n}.com")
    domain_status = DomainStatus.active
    technical_owner = factory.SubFactory(UserFactory)
    business_owner = factory.SubFactory(UserFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)
    dns_provider = factory.SubFactory(DNSProviderFactory)

    class Meta:
        model = Domain

    @factory.post_generation
    def post_additional_services(self, create, extracted, **kwargs):
        self.additional_services.add(DomainProviderAdditionalServicesFactory())


class DomainContractFactory(DjangoModelFactory):
    domain = factory.SubFactory(DomainFactory)

    class Meta:
        model = DomainContract
