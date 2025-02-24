from datetime import datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal, FuzzyInteger

from ralph.assets.models.choices import AssetSource
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    BaseObjectFactory,
    BudgetInfoFactory,
    ConfigurationClassFactory,
    DataCenterAssetModelFactory,
    DiskFactory,
    EthernetFactory,
    EthernetWithIPAddressFactory,
    FibreChannelCardFactory,
    MemoryFactory,
    ProcessorFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.models import BaseObjectCluster
from ralph.data_center.models.choices import ConnectionType
from ralph.data_center.models.components import DiskShare, DiskShareMount
from ralph.data_center.models.physical import (
    Accessory,
    ACCESSORY_DATA,
    Connection,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom
)
from ralph.data_center.models.virtual import (
    Cluster,
    ClusterType,
    Database,
    VIP,
    VIPProtocol
)
from ralph.security.tests.factories import SecurityScanFactory

date_now = datetime.now().date()


class DiskShareFactory(DjangoModelFactory):
    base_object = factory.SubFactory(BaseObjectFactory)
    wwn = factory.Sequence(lambda n: "wwn {}".format(n))

    class Meta:
        model = DiskShare


class DiskShareMountFactory(DjangoModelFactory):
    share = factory.SubFactory(DiskShareFactory)

    class Meta:
        model = DiskShareMount


class ClusterTypeFactory(DjangoModelFactory):
    name = factory.Iterator(["Application", "Partitional"])

    class Meta:
        model = ClusterType
        django_get_or_create = ["name"]


class ClusterFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Cluster {n}")
    type = factory.SubFactory(ClusterTypeFactory)
    configuration_path = factory.SubFactory(ConfigurationClassFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Cluster
        django_get_or_create = ["name"]

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add("abc, cde", "xyz")


class BaseObjectClusterFactory(DjangoModelFactory):
    cluster = factory.SubFactory(ClusterFactory)
    base_object = factory.SubFactory(BaseObjectFactory)

    class Meta:
        model = BaseObjectCluster
        django_get_or_create = ["cluster", "base_object"]


class DataCenterFactory(DjangoModelFactory):
    name = factory.Iterator(["DC1", "DC2", "DC3", "DC4", "DC5"])

    class Meta:
        model = DataCenter
        django_get_or_create = ["name"]


class ServerRoomFactory(DjangoModelFactory):
    name = factory.Iterator(
        ["Server Room A", "Server Room B", "Server Room C", "Server Room D"]
    )
    data_center = factory.SubFactory(DataCenterFactory)

    class Meta:
        model = ServerRoom
        django_get_or_create = ["name"]


class AccessoryFactory(DjangoModelFactory):
    name = factory.Iterator(ACCESSORY_DATA)

    class Meta:
        model = Accessory
        django_get_or_create = ["name"]


class RackFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Rack #{}".format(n + 100))
    server_room = factory.SubFactory(ServerRoomFactory)

    class Meta:
        model = Rack
        django_get_or_create = ["name"]


class RackAccessoryFactory(DjangoModelFactory):
    accessory = factory.SubFactory(AccessoryFactory)
    rack = factory.SubFactory(RackFactory)

    class Meta:
        model = RackAccessory


class DataCenterAssetFactory(DjangoModelFactory):
    force_depreciation = False
    model = factory.SubFactory(DataCenterAssetModelFactory)
    sn = factory.Faker("ssn")
    barcode = factory.Sequence(lambda n: "dc" + str(n + 10**8))
    hostname = factory.Sequence(lambda n: "ralph{}.allegro.pl".format(n))
    order_no = factory.Sequence(lambda n: "Order number " + str(n))
    budget_info = factory.SubFactory(BudgetInfoFactory)
    invoice_date = date_now - timedelta(days=15)
    invoice_no = factory.Sequence(lambda n: "Invoice number " + str(n))
    property_of = factory.SubFactory(AssetHolderFactory)
    provider = factory.Iterator(["Komputronik", "Dell Poland", "Oracle Poland"])
    source = factory.Iterator([AssetSource.shipment.id, AssetSource.salvaged.id])
    price = FuzzyDecimal(10, 300)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)
    configuration_path = factory.SubFactory(ConfigurationClassFactory)
    firmware_version = factory.Sequence(lambda n: "1.1.{}".format(n))
    bios_version = factory.Sequence(lambda n: "2.2.{}".format(n))

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
        "base_object",
        ipaddress__is_management=True,
    )
    eth2 = factory.RelatedFactory(EthernetFactory, "base_object")
    eth3 = factory.RelatedFactory(
        EthernetWithIPAddressFactory,
        "base_object",
        ipaddress__dhcp_expose=True,
    )
    licence1 = factory.RelatedFactory(
        "ralph.licences.tests.factories.BaseObjectLicenceFactory", "base_object"
    )
    licence2 = factory.RelatedFactory(
        "ralph.licences.tests.factories.BaseObjectLicenceFactory",
        "base_object",
        quantity=3,
    )
    support1 = factory.RelatedFactory(
        "ralph.supports.tests.factories.BaseObjectsSupportFactory", "baseobject"
    )
    support2 = factory.RelatedFactory(
        "ralph.supports.tests.factories.BaseObjectsSupportFactory", "baseobject"
    )
    mem1 = factory.RelatedFactory(MemoryFactory, "base_object")
    mem2 = factory.RelatedFactory(MemoryFactory, "base_object")
    fc_card1 = factory.RelatedFactory(FibreChannelCardFactory, "base_object")
    fc_card2 = factory.RelatedFactory(FibreChannelCardFactory, "base_object")
    proc1 = factory.RelatedFactory(ProcessorFactory, "base_object")
    proc2 = factory.RelatedFactory(ProcessorFactory, "base_object")
    disk1 = factory.RelatedFactory(DiskFactory, "base_object")
    disk2 = factory.RelatedFactory(DiskFactory, "base_object")
    scmstatuscheck = factory.RelatedFactory(
        "ralph.configuration_management.tests.factories.SCMStatusCheckFactory",
        "base_object",
    )
    securityscan = factory.RelatedFactory(
        SecurityScanFactory, factory_related_name="base_object"
    )

    securityscan = factory.RelatedFactory(SecurityScanFactory, "base_object")

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add("abc, cde", "xyz")


class ConnectionFactory(DjangoModelFactory):
    outbound = factory.SubFactory(DataCenterAssetFactory)
    inbound = factory.SubFactory(DataCenterAssetFactory)
    connection_type = factory.Iterator([ConnectionType.network.id])

    class Meta:
        model = Connection


class DatabaseFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = Database


class VIPFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "ralph-test{}.local".format(n))
    # IPAddressFactory is given as string to avoid circular imports here.
    ip = factory.SubFactory("ralph.networks.tests.factories.IPAddressFactory")
    port = FuzzyInteger(1024, 49151)
    protocol = factory.Iterator([VIPProtocol.TCP.id, VIPProtocol.UDP.id])
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = VIP


class VIPFullFactory(VIPFactory):
    parent = factory.SubFactory(Cluster)
