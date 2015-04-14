#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory

from ralph.account.models import Region
from ralph.business.models import (
    Venture, VentureRole, RolePropertyType, RoleProperty,
)
from ralph.cmdb import models_ci
from ralph.cmdb.tests.utils import CIFactory
from ralph.ui.tests.global_utils import UserFactory


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class BusinessLineFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='BusinessLine')


class ProfitCenterFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='ProfitCenter')


class ServiceFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='Service')


class EnvironmentFactory(CIFactory):
    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(name='Environment')


@factory.sequence
def get_profile(n):
    """Due to strange logic in lck.django we can't use subfactories to create
    profiles."""
    user = UserFactory()
    user.save()
    return user.profile


class CIOwnerFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIOwner
    profile = get_profile


class ServiceOwnershipFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIOwnership
    owner = factory.SubFactory(CIOwnerFactory)
    ci = factory.SubFactory(ServiceFactory)


class ServiceEnvironmentRelationFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIRelation
    parent = factory.SubFactory(ServiceFactory)
    child = factory.SubFactory(EnvironmentFactory)
    type = models_ci.CI_RELATION_TYPES.HASROLE
    readonly = False


class ServiceProfitCenterRelationFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIRelation
    parent = factory.SubFactory(ProfitCenterFactory)
    child = factory.SubFactory(ServiceFactory)
    type = models_ci.CI_RELATION_TYPES.CONTAINS
    readonly = False


class RegionFactory(DjangoModelFactory):
    FACTORY_FOR = Region
    name = factory.Sequence(lambda n: 'Region #{}'.format(n))


class VentureFactory(DjangoModelFactory):
    FACTORY_FOR = Venture
    name = factory.Sequence(lambda n: 'Venture #{}'.format(n))


class VentureRoleFactory(DjangoModelFactory):
    FACTORY_FOR = VentureRole
    name = factory.Sequence(lambda n: 'Venture role #{}'.format(n))
    venture = factory.SubFactory(VentureFactory)


class RolePropertyTypeFactory(DjangoModelFactory):
    FACTORY_FOR = RolePropertyType
    symbol = factory.Sequence(lambda n: 'property_type_{}'.format(n))


class RolePropertyFactory(DjangoModelFactory):
    FACTORY_FOR = RoleProperty
    symbol = factory.Sequence(lambda n: 'property_{}'.format(n))
    type = factory.SubFactory(RolePropertyTypeFactory)
