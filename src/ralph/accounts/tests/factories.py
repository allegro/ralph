# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.models import RalphUser, Region


class RegionFactory(DjangoModelFactory):

    name = factory.Iterator(['pl', 'de', 'ua'])


    class Meta:
        model = Region
        django_get_or_create = ['name']


class UserFactory(DjangoModelFactory):

    username = factory.Sequence(lambda n: 'user ' + str(n))
    is_active = True

    class Meta:
        model = RalphUser
