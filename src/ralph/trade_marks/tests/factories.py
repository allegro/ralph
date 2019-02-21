# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import factory
from dj.choices import Country
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import AssetHolderFactory

from ralph.domains.tests.factories import DomainFactory
from ralph.trade_marks.models import (
    ProviderAdditionalMarking,
    TradeMark,
    TradeMarkAdditionalCountry,
    TradeMarkCountry,
    TradeMarksLinkedDomains
    )


date_now = datetime.now().date()


class TradeMarkFactory(DjangoModelFactory):
    valid_to = date_now + timedelta(days=365)
    registrant_number = factory.Sequence(lambda n: 'Registrant number ' + str(n))
    name = factory.Sequence(lambda n: 'Trade Mark name ' + str(n))
    technical_owner = factory.SubFactory(UserFactory)
    business_owner = factory.SubFactory(UserFactory)
    registrant_class = factory.Sequence(lambda n: 'Registrant class ' + str(n))
    holder = factory.SubFactory(AssetHolderFactory)

    class Meta:
        model = TradeMark


class TradeMarkRegistrarInstitutionFactory(DjangoModelFactory):
    name = factory.Iterator(['WNIP', 'WIP', 'PUP'])


class TradeMarkCountryFactory(DjangoModelFactory):
    country = factory.Faker(
        'random_element', elements=[x[0] for x in TradeMarkCountry.country]
    )

    class Meta:
        model = TradeMarkCountry


class TradeMarksLinkedDomainsFactory(DjangoModelFactory):
    trade_mark = factory.SubFactory(TradeMarkFactory)
    domain = factory.SubFactory(DomainFactory)

    class Meta:
        model = TradeMarksLinkedDomains


class ProviderAdditionalMarkingFactory(DjangoModelFactory):
    name = factory.Iterator(['Masking', 'Backside', 'Acquisition'])

    class Meta:
        model = ProviderAdditionalMarking
        django_get_or_create = ['name']


class TradeMarkAdditionalCountryFactory(DjangoModelFactory):
    trade_mark = factory.SubFactory(TradeMarkFactory)
    country = factory.SubFactory(TradeMarkCountryFactory)

    class Meta:
        model = TradeMarkAdditionalCountry
