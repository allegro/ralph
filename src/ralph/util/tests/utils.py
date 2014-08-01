#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory

from ralph.cmdb import models_ci
from ralph.cmdb.tests.utils import CIFactory


class BusinessLineFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='BusinessLine')


class ServiceFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='Service')


class CIOwnerFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIOwner
    first_name = 'Some'
    last_name = factory.Sequence(lambda n: 'Owner #{}'.format(n))
    email = factory.Sequence(lambda n: 'some.owner{}@ex.com'.format(n))
    sAMAccountName = 'qwerty'


class ServiceOwnershipFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIOwnership
    owner = factory.SubFactory(CIOwnerFactory)
    ci = factory.SubFactory(ServiceFactory)


class ServiceBusinessLineRelationFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIRelation
    parent = factory.SubFactory(BusinessLineFactory)
    child = factory.SubFactory(ServiceFactory)
    type = models_ci.CI_RELATION_TYPES.CONTAINS
    readonly = False
