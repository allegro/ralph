import factory
from factory.django import DjangoModelFactory

from ralph.access_cards.models import AccessCard, AccessCardStatus
from ralph.accounts.tests.factories import RegionFactory


class AccessCardFactory(DjangoModelFactory):
    visual_number = factory.Sequence(lambda n: '000000000000{}'.format(n))
    system_number = factory.Sequence(lambda n: '000000000000{}'.format(n))
    region = factory.SubFactory(RegionFactory)
    status = AccessCardStatus.new

    class Meta:
        model = AccessCard
        django_get_or_create = ['visual_number', 'system_number']
