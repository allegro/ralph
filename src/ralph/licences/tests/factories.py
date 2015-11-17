# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.assets.tests.factories import ManufacturerFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)


class LicenceTypeFactory(DjangoModelFactory):

    name = factory.Iterator(['Processor', 'MSDN', 'VL (per core)'])

    class Meta:
        model = LicenceType
        django_get_or_create = ['name']


class SoftwareFactory(DjangoModelFactory):

    name = factory.Iterator(['Oracle', 'Project Info', 'Jira'])

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

    class Meta:
        model = Licence


class LicenceUserFactory(DjangoModelFactory):
    licence = factory.SubFactory(LicenceFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = LicenceUser


class BaseObjectLicence(DjangoModelFactory):
    licence = factory.SubFactory(LicenceFactory)
    base_object = factory.SubFactory(BackOfficeAssetFactory)

    class Meta:
        model = BaseObjectLicence


class LicenceWithUserAndBaseObjectsFactory(LicenceFactory):
    users = factory.RelatedFactory(LicenceUserFactory, 'licence')
    base_objects = factory.RelatedFactory(BaseObjectLicence, 'licence')
