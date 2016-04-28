import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.assets.tests.factories import BaseObjectFactory
from ralph.data_center.tests.factories import DataCenterFactory
from ralph.networks.models.networks import (
    IPAddress,
    Network,
    NetworkEnvironment
)


class NetworkEnvironmentFactory(DjangoModelFactory):
    name = factory.Iterator(['DC1', 'DC2', 'Warehouse'])
    data_center = factory.SubFactory(DataCenterFactory)
    hostname_template_prefix = 's1'
    hostname_template_postfix = '.mydc.net'

    class Meta:
        model = NetworkEnvironment
        django_get_or_create = ['name']


class NetworkFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Network #' + str(n))
    network_environment = factory.SubFactory(NetworkEnvironmentFactory)

    class Meta:
        model = Network


class IPAddressFactory(DjangoModelFactory):
    address = factory.Faker('ipv4')
    hostname = FuzzyText(
        prefix='ralph.', suffix='.allegro.pl', length=40
    )
    base_object = factory.SubFactory(BaseObjectFactory)

    class Meta:
        model = IPAddress


class ManagementIPAddressFactory(DjangoModelFactory):
    is_management = True

    class Meta:
        model = IPAddress
