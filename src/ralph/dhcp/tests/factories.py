import factory
from factory.django import DjangoModelFactory

from ralph.dhcp.models import DHCPServer, DNSServer


class DNSServerFactory(DjangoModelFactory):
    ip_address = factory.Faker('ipv4')

    class Meta:
        model = DNSServer


class DHCPServerFactory(DjangoModelFactory):
    ip = factory.Faker('ipv4')

    class Meta:
        model = DHCPServer
