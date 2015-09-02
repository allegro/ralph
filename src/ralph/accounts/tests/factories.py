# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.models import Region


class RegionFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Region {}'.format(n))

    class Meta:
        model = Region
