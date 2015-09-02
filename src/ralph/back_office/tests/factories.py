# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.tests.factories import BackOfficeAssetModelFactory
from ralph.back_office.models import BackOfficeAsset, Warehouse


class WarehouseFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Warehouse {}'.format(n))

    class Meta:
        model = Warehouse


class BackOfficeAssetFactory(DjangoModelFactory):

    hostname = factory.Sequence(lambda n: 'c%04d' % n)
    region = factory.SubFactory(RegionFactory)
    model = factory.SubFactory(BackOfficeAssetModelFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    force_depreciation = False

    class Meta:
        model = BackOfficeAsset
