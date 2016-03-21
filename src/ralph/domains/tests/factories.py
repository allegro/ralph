# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.domains.models import Domain, DomainStatus


class DomainFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'www.domain{}.com'.format(n))
    domain_status = DomainStatus.active

    class Meta:
        model = Domain
