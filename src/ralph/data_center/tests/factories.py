# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory

from ralph.data_center.models.physical import (
    Accessory,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom,
)


class DataCenterFactory(DjangoModelFactory):

    name = factory.Iterator(['DC1', 'DC2', 'DC3', 'DC4', 'DC5'])

    class Meta:
        model = DataCenter
        django_get_or_create = ['name']


class ServerRoomFactory(DjangoModelFactory):

    name = factory.Iterator([
        'Server Room A', 'Server Room B', 'Server Room C'
    ])
    data_center = factory.SubFactory(DataCenterFactory)

    class Meta:
        model = ServerRoom
        django_get_or_create = ['name']


class AccessoryFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Accesory #{}'.format(n))

    class Meta:
        model = Accessory


class RackAccessoryFactory(DjangoModelFactory):

    class Meta:
        model = RackAccessory


class RackFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Rack #{}'.format(n + 100))

    class Meta:
        model = Rack
        django_get_or_create = ['name']


class DataCenterAssetFactory(DjangoModelFactory):

    class Meta:
        model = DataCenterAsset
