from factory.django import DjangoModelFactory
from factory import SubFactory, Sequence, post_generation

from ralph.accessories.models import AccessoryStatus
from ralph.assets.tests.factories import CategoryFactory, ManufacturerFactory
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.tests.factories import UserFactory


class AccessoryFactory(DjangoModelFactory):
    manufacturer = SubFactory(ManufacturerFactory)
    category = SubFactory(CategoryFactory)
    accessory_name = Sequence(lambda n: 'Accessory {}'.format(n))
    product_number = Sequence(lambda n: 'Product number {}'.format(n))
    owner = SubFactory(UserFactory)
    status = AccessoryStatus.new
    number_bought = 1
    warehouse = SubFactory(WarehouseFactory)

    @post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.user.add(user)
        else:
            self.user.add(UserFactory())
