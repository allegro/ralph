from datetime import datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal, FuzzyText

from ralph.assets.models.choices import AssetSource
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    BaseObjectFactory,
    BudgetInfoFactory,
    DataCenterAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.models.networks import IPAddress
from ralph.data_center.models.physical import (
    Accessory,
    ACCESSORY_DATA,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
)
from ralph.data_center.models.virtual import Cluster, ClusterType, Database, VIP

date_now = datetime.now().date()


class ClusterTypeFactory(DjangoModelFactory):

    name = factory.Iterator(['Application', 'Partitional'])

    class Meta:
        model = ClusterType
        django_get_or_create = ['name']


class ClusterFactory(DjangoModelFactory):

    name = factory.Iterator(['Databases', 'Applications'])
    type = factory.SubFactory(ClusterTypeFactory)

    class Meta:
        model = Cluster
        django_get_or_create = ['name']


class DataCenterFactory(DjangoModelFactory):

    name = factory.Iterator(['DC1', 'DC2', 'DC3', 'DC4', 'DC5'])

    class Meta:
        model = DataCenter
        django_get_or_create = ['name']


class ServerRoomFactory(DjangoModelFactory):

    name = factory.Iterator([
        'Server Room A', 'Server Room B', 'Server Room C', 'Server Room D'
    ])
    data_center = factory.SubFactory(DataCenterFactory)

    class Meta:
        model = ServerRoom
        django_get_or_create = ['name']


class AccessoryFactory(DjangoModelFactory):

    name = factory.Iterator(ACCESSORY_DATA)

    class Meta:
        model = Accessory
        django_get_or_create = ['name']


class RackAccessoryFactory(DjangoModelFactory):

    class Meta:
        model = RackAccessory


class RackFactory(DjangoModelFactory):

    name = factory.Sequence(lambda n: 'Rack #{}'.format(n + 100))

    class Meta:
        model = Rack
        django_get_or_create = ['name']


class DataCenterAssetFactory(DjangoModelFactory):
    force_depreciation = False
    model = factory.SubFactory(DataCenterAssetModelFactory)
    sn = factory.Faker('ssn')
    barcode = factory.Faker('ean8')
    hostname = factory.Sequence(lambda n: 'ralph{}.allegro.pl'.format(n))
    order_no = factory.Sequence(lambda n: 'Order number ' + str(n))
    budget_info = factory.SubFactory(BudgetInfoFactory)
    invoice_date = date_now - timedelta(days=15)
    invoice_no = factory.Sequence(lambda n: 'Invoice number ' + str(n))
    property_of = factory.SubFactory(AssetHolderFactory)
    provider = factory.Iterator([
        'Komputronik', 'Dell Poland', 'Oracle Poland'
    ])
    source = factory.Iterator([
        AssetSource.shipment.id, AssetSource.salvaged.id
    ])
    price = FuzzyDecimal(10, 300)
    management_ip = factory.Faker('ipv4')
    management_hostname = FuzzyText(
        prefix='ralph.', suffix='.allegro.pl', length=40
    )

    class Meta:
        model = DataCenterAsset


class IPAddressFactory(DjangoModelFactory):
    base_object = factory.SubFactory(BaseObjectFactory)

    class Meta:
        model = IPAddress


class DatabaseFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Database


class VIPFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = VIP
