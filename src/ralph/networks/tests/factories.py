import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.assets.tests.factories import BaseObjectFactory
from ralph.networks.models.networks import IPAddress


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
