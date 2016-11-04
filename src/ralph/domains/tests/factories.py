# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.domains.models import (
    Domain,
    DomainContract,
    DomainRegistrant,
    DomainStatus
)


class DomainFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'www.domain{}.com'.format(n))
    domain_status = DomainStatus.active
    technical_owner = factory.SubFactory(UserFactory)
    business_owner = factory.SubFactory(UserFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Domain


class DomainContractFactory(DjangoModelFactory):

    domain = factory.SubFactory(DomainFactory)

    class Meta:
        model = DomainContract


class DomainRegistrantFactory(DjangoModelFactory):

    name = factory.Iterator(['ovh', 'home.pl', 'nazwa.pl'])

    class Meta:
        model = DomainRegistrant
        django_get_or_create = ['name']
