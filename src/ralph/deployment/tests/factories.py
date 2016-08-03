import factory
from factory.django import DjangoModelFactory

from ralph.deployment.models import Preboot, PrebootConfiguration


class PrebootFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Preboot {}'.format(n))

    class Meta:
        model = Preboot


class PrebootConfigurationFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'PrebootConfiguration {}'.format(n))

    class Meta:
        model = PrebootConfiguration
