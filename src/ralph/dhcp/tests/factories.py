import factory
from factory.django import DjangoModelFactory

from ralph.dhcp.models import DNSServer


class DNSServerFactory(DjangoModelFactory):
    ip_address = factory.Faker('ipv4')

    class Meta:
        model = DNSServer
