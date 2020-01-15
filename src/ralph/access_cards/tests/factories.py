import factory
from factory.django import DjangoModelFactory

from ralph.access_cards.models import AccessCard, AccessCardStatus


class AccessCardFactory(DjangoModelFactory):
    visual_number = factory.Sequence(lambda n: '000000000000{}'.format(n))
    system_number = factory.Sequence(lambda n: '000000000000{}'.format(n))
    status = AccessCardStatus.new

    class Meta:
        model = AccessCard
        django_get_or_create = ['visual_number', 'system_number']
