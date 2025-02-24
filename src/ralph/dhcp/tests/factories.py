import factory
from factory.django import DjangoModelFactory

from ralph.dhcp.models import (
    DHCPServer,
    DNSServer,
    DNSServerGroup,
    DNSServerGroupOrder
)


class DNSServerFactory(DjangoModelFactory):
    ip_address = factory.Faker("ipv4")

    class Meta:
        model = DNSServer


class DHCPServerFactory(DjangoModelFactory):
    ip = factory.Faker("ipv4")

    class Meta:
        model = DHCPServer


class DNSServerGroupFactory(DjangoModelFactory):
    name = factory.Faker("name")

    class Meta:
        model = DNSServerGroup


class DNSServerGroupOrderFactory(DjangoModelFactory):
    dns_server_group = factory.SubFactory(DNSServerGroupFactory)
    dns_server = factory.SubFactory(DNSServerFactory)
    order = 0

    class Meta:
        model = DNSServerGroupOrder
