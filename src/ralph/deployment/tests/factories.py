import factory
from factory.django import DjangoModelFactory

from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.deployment.models import Deployment, Preboot, PrebootConfiguration


class PrebootFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Preboot {}".format(n))

    class Meta:
        model = Preboot


class PrebootConfigurationFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "PrebootConfiguration {}".format(n))

    class Meta:
        model = PrebootConfiguration


def _get_deployment():
    obj = DataCenterAssetFullFactory()
    return Deployment(obj=obj)
