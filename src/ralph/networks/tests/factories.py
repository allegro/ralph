import ipaddress

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.assets.tests.factories import EthernetFactory
from ralph.data_center.tests.factories import DataCenterFactory
from ralph.networks.models.networks import (
    IPAddress,
    Network,
    NetworkEnvironment,
    NetworkKind
)


class NetworkKindFactory(DjangoModelFactory):
    name = factory.Iterator(['office', 'DC', 'HA', 'L3'])

    class Meta:
        model = NetworkKind
        django_get_or_create = ['name']


class NetworkEnvironmentFactory(DjangoModelFactory):
    name = factory.Iterator(['prod1', 'test1', 'preprod1', 'dev1'])
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
    ethernet = factory.SubFactory(EthernetFactory)

    class Meta:
        model = IPAddress


def _get_network_address(ip, mask=24):
    """
    Return address of the IPv4 network for single IPv4 address with given mask.
    """
    ip = ipaddress.ip_address(ip)
    return ipaddress.ip_network(
        '{}/{}'.format(
            ipaddress.ip_address(int(ip) & (2**32 - 1) << (32 - mask)),
            mask
        )
    )


class IPAddressWithNetworkFactory(IPAddressFactory):
    network = factory.SubFactory(
        NetworkFactory,
        address=factory.LazyAttribute(
            lambda ipaddress: _get_network_address(
                ipaddress.factory_parent.address
            )
        )
    )


class ManagementIPAddressFactory(DjangoModelFactory):
    is_management = True

    class Meta:
        model = IPAddress
