#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User

from ralph.account.models import Profile
from ralph.cmdb import models_ci
from ralph.cmdb.tests.utils import CIFactory


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

class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    first_name = factory.Sequence(lambda n: 'John {0}'.format(n))
    last_name = factory.Sequence(lambda n: 'Snow {0}'.format(n))

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
