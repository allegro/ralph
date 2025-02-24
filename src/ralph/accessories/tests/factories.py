from factory import post_generation, Sequence, SubFactory
from factory.django import DjangoModelFactory

from ralph.accessories.models import Accessory, AccessoryStatus, AccessoryUser
from ralph.accounts.tests.factories import RegionFactory, UserFactory
from ralph.assets.tests.factories import CategoryFactory, ManufacturerFactory
from ralph.back_office.tests.factories import WarehouseFactory


class AccessoryFactory(DjangoModelFactory):
    manufacturer = SubFactory(ManufacturerFactory)
    category = SubFactory(CategoryFactory)
    accessory_name = Sequence(lambda n: "Accessory {}".format(n))
    product_number = Sequence(lambda n: "Product number {}".format(n))
    owner = SubFactory(UserFactory)
    status = AccessoryStatus.new
    number_bought = 1
    warehouse = SubFactory(WarehouseFactory)
    region = SubFactory(RegionFactory)

    @post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.user.set([user for user in extracted])
        else:
            acu = AccessoryUser(user=UserFactory(), accessory=self, quantity=1)
            acu.save()

    class Meta:
        model = Accessory
