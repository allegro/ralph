import factory
from factory.django import DjangoModelFactory

from ralph.assets.tests.factories import BaseObjectFactory
from ralph.networks.models.networks import IPAddress


class IPAddressFactory(DjangoModelFactory):
    base_object = factory.SubFactory(BaseObjectFactory)

    class Meta:
        model = IPAddress
