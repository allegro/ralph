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
    DomainStatus
)
from ralph.domains.models.domains import DomainProviderAdditionalServices


class DomainFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "www.domain{}.com".format(n))
    domain_status = DomainStatus.active
    technical_owner = factory.SubFactory(UserFactory)
    business_owner = factory.SubFactory(UserFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Domain


class DNSProviderFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "dns-provider{}".format(n))

    class Meta:
        model = DNSProvider


class DomainCategoryFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "domain-contract{}".format(n))

    class Meta:
        model = DomainCategory


class DomainContractFactory(DjangoModelFactory):
    domain = factory.SubFactory(DomainFactory)

    class Meta:
        model = DomainContract


class DomainRegistrantFactory(DjangoModelFactory):
    name = factory.Iterator(["ovh", "home.pl", "nazwa.pl"])

    class Meta:
        model = DomainRegistrant
        django_get_or_create = ["name"]


class DomainProviderAdditionalServicesFactory(DjangoModelFactory):
    name = factory.Iterator(["Masking", "Backorder", "Acquisition"])

    class Meta:
        model = DomainProviderAdditionalServices
        django_get_or_create = ["name"]
