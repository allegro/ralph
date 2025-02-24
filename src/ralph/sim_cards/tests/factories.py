import factory
from factory.django import DjangoModelFactory

from ralph.back_office.models import BackOfficeAssetStatus
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.sim_cards.models import CellularCarrier, SIMCard, SIMCardFeatures


class CellularCarrierFactory(DjangoModelFactory):
    name = factory.Iterator(["Mobile One", "Mobile Two", "Mobile T"])

    class Meta:
        model = CellularCarrier
        django_get_or_create = ["name"]


class SIMCardFeatureFactory(DjangoModelFactory):
    name = factory.Iterator(["Feature {}".format(a) for a in range(50)])

    class Meta:
        model = SIMCardFeatures
        django_get_or_create = ["name"]


class SIMCardFactory(DjangoModelFactory):
    remarks = factory.Sequence(lambda n: "Generated factory {}".format(n))
    pin1 = factory.Sequence(lambda n: "0000{}".format(n))
    pin2 = factory.Sequence(lambda n: "0000{}".format(n))
    puk1 = factory.Sequence(lambda n: "00000000{}".format(n))
    puk2 = factory.Sequence(lambda n: "00000000{}".format(n))
    card_number = factory.Sequence(lambda n: "00{}000{}000".format(n, n))
    phone_number = factory.Sequence(lambda n: "+48{}000{}000".format(n, n))
    warehouse = factory.SubFactory(WarehouseFactory)
    carrier = factory.SubFactory(CellularCarrierFactory)
    status = BackOfficeAssetStatus.new

    class Meta:
        model = SIMCard
        django_get_or_create = ["card_number"]
