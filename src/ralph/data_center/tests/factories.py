from datetime import datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal

from ralph.assets.models.choices import AssetSource
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    BudgetInfoFactory,
    ConfigurationClassFactory,
    DataCenterAssetModelFactory,
    EthernetFactory,
    EthernetWithIPAddressFactory,
    FibreChannelCardFactory,
    MemoryFactory,
    ProcessorFactory,
    ServiceEnvironmentFactory
)
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
    configuration_path = factory.SubFactory(ConfigurationClassFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Cluster
        django_get_or_create = ['name']

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add('abc, cde', 'xyz')


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
    server_room = factory.SubFactory(ServerRoomFactory)

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
    service_env = factory.SubFactory(ServiceEnvironmentFactory)
    configuration_path = factory.SubFactory(ConfigurationClassFactory)

    class Meta:
        model = DataCenterAsset


class DataCenterAssetFullFactory(DataCenterAssetFactory):
    """
    Factory for DataCenterAsset and m2m relations
    """
    rack = factory.SubFactory(RackFactory)

    # m2m relations
    # TODO: parent, networks (as terminators), operations, security scans,
    # clusters, tags
    eth1 = factory.RelatedFactory(
        EthernetWithIPAddressFactory,
        'base_object',
        ipaddress__is_management=True,
    )
    eth2 = factory.RelatedFactory(EthernetFactory, 'base_object')
    eth3 = factory.RelatedFactory(
        EthernetWithIPAddressFactory,
        'base_object',
        ipaddress__dhcp_expose=True,
    )
    licence1 = factory.RelatedFactory(
        'ralph.licences.tests.factories.BaseObjectLicenceFactory', 'base_object'
    )
    licence2 = factory.RelatedFactory(
        'ralph.licences.tests.factories.BaseObjectLicenceFactory',
        'base_object',
        quantity=3
    )
    support1 = factory.RelatedFactory(
        'ralph.supports.tests.factories.BaseObjectsSupportFactory',
        'baseobject'
    )
    support2 = factory.RelatedFactory(
        'ralph.supports.tests.factories.BaseObjectsSupportFactory',
        'baseobject'
    )
    mem1 = factory.RelatedFactory(MemoryFactory, 'base_object')
    mem2 = factory.RelatedFactory(MemoryFactory, 'base_object')
    fc_card1 = factory.RelatedFactory(FibreChannelCardFactory, 'base_object')
    fc_card2 = factory.RelatedFactory(FibreChannelCardFactory, 'base_object')
    proc1 = factory.RelatedFactory(ProcessorFactory, 'base_object')
    proc2 = factory.RelatedFactory(ProcessorFactory, 'base_object')

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add('abc, cde', 'xyz')


class DatabaseFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Database


class VIPFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = VIP
