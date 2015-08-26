# -*- coding: utf-8 -*-
from datetime import date

import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import RegionFactory
from ralph.supports.models import Support, SupportStatus, SupportType


class SupportTypeFactory(DjangoModelFactory):

    name = 'warranty'

    class Meta:
        model = SupportType


class SupportFactory(DjangoModelFactory):

    region = factory.SubFactory(RegionFactory)
    support_type = factory.SubFactory(SupportTypeFactory)
    status = SupportStatus.new
    contract_id = factory.Sequence(lambda n: 'c{}'.format(n))
    date_to = date(2020, 12, 31)

    class Meta:
        model = Support
