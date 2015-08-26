# -*- coding: utf-8 -*-
from factory.django import DjangoModelFactory

from ralph.accounts.models import Region


class RegionFactory(DjangoModelFactory):

    class Meta:
        model = Region
