# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    BudgetInfoFactory,
    ManufacturerFactory
)
from ralph.back_office.tests.factories import (
    BackOfficeAssetFactory,
    OfficeInfrastructureFactory
)
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)

date_now = datetime.now().date()


class LicenceTypeFactory(DjangoModelFactory):

    name = factory.Iterator([
        'per user', 'per install', 'msdn', 'disk drive', 'vl (per core)'
    ])

    class Meta:
        model = LicenceType
        django_get_or_create = ['name']


class SoftwareFactory(DjangoModelFactory):

    name = factory.Iterator([
        'MS EA CoreCal', 'DB Boost', 'Twilio', 'Infographics',
        'Oracle Business Intelligence Server Administrator',
        'Oracle Advanced Compression'
    ])

    class Meta:
        model = Software
        django_get_or_create = ['name']


class LicenceFactory(DjangoModelFactory):

    licence_type = factory.SubFactory(LicenceTypeFactory)
    software = factory.SubFactory(SoftwareFactory)
    region = factory.SubFactory(RegionFactory)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    niw = FuzzyText()
    number_bought = 10
    invoice_date = date_now - timedelta(days=15)
    valid_thru = date_now + timedelta(days=365)
    invoice_no = factory.Sequence(lambda n: 'Invoice number ' + str(n))
    budget_info = factory.SubFactory(BudgetInfoFactory)
    sn = factory.Faker('ssn')
    order_no = factory.Sequence(lambda n: 'Order number ' + str(n))
    property_of = factory.SubFactory(AssetHolderFactory)
    office_infrastructure = factory.SubFactory(OfficeInfrastructureFactory)

    class Meta:
        model = Licence


class LicenceUserFactory(DjangoModelFactory):
    licence = factory.SubFactory(LicenceFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = LicenceUser


class BaseObjectLicenceFactory(DjangoModelFactory):
    licence = factory.SubFactory(LicenceFactory)
    base_object = factory.SubFactory(BackOfficeAssetFactory)

    class Meta:
        model = BaseObjectLicence


class BaseObjectDataCenterLicenceFactory(DjangoModelFactory):
    licence = factory.SubFactory(LicenceFactory)
    base_object = factory.SubFactory(DataCenterAssetFactory)

    class Meta:
        model = BaseObjectLicence


class LicenceWithUserAndBaseObjectsFactory(LicenceFactory):
    users = factory.RelatedFactory(LicenceUserFactory, 'licence')
    base_objects = factory.RelatedFactory(BaseObjectLicenceFactory, 'licence')
