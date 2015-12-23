import factory
from factory.django import DjangoModelFactory

from ralph.assets.tests.factories import (
    BaseObjectFactory,
    DataCenterAssetModelFactory
)
from ralph.data_center.models.networks import IPAddress
from ralph.data_center.models.physical import (
    Accessory,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
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
    force_depreciation = False
    model = factory.SubFactory(DataCenterAssetModelFactory)
    hostname = factory.Sequence(lambda n: 'hostname #{}'.format(n))

    class Meta:
        model = DataCenterAsset


class IPAddressFactory(DjangoModelFactory):
    base_object = factory.SubFactory(BaseObjectFactory)

    class Meta:
        model = IPAddress
