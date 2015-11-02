# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import RegionFactory
from ralph.licences.models import Licence, LicenceType, Software


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

    region = factory.SubFactory(RegionFactory)
    licence_type = factory.SubFactory(LicenceTypeFactory)
    software = factory.SubFactory(SoftwareFactory)

    class Meta:
        model = Licence
