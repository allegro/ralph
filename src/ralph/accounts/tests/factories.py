# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.models import Region


class RegionFactory(DjangoModelFactory):

    name = factory.Iterator(['pl', 'de', 'ua'])


    class Meta:
        model = Region
        django_get_or_create = ['name']
