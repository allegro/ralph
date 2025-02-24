import factory
from factory.django import DjangoModelFactory

from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    DiskFactory,
    EthernetFactory,
    EthernetWithIPAddressFactory,
    MemoryFactory,
    ProcessorFactory,
    ServiceEnvironmentFactory
)
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.security.tests.factories import SecurityScanFactory
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudImage,
    CloudProject,
    CloudProvider,
    VirtualServer,
    VirtualServerType
)


class CloudImageFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "image-{0}".format(n))
    image_id = factory.Sequence(lambda n: "img-uuid-{0}".format(n))

    class Meta:
        model = CloudImage
        django_get_or_create = ["name", "image_id"]


class CloudProviderFactory(DjangoModelFactory):
    name = factory.Iterator(["openstack", "openstack2"])
    cloud_sync_enabled = False
    cloud_sync_driver = factory.Iterator(["noop"])

    class Meta:
        model = CloudProvider
        django_get_or_create = ["name"]


class CloudFlavorFactory(DjangoModelFactory):
    name = factory.Iterator(["flavor1", "flavor2", "flavor3"])
    flavor_id = factory.Iterator(["flavor_id1", "flavor_id2", "flavor_id3"])
    cloudprovider = factory.SubFactory(CloudProviderFactory, name="openstack")

    class Meta:
        model = CloudFlavor
        django_get_or_create = ["flavor_id"]


class CloudProjectFactory(DjangoModelFactory):
    name = factory.Iterator(["project1", "project2", "project3"])
    project_id = factory.Iterator(["project_id1", "project_id2", "project_id3"])
    cloudprovider = factory.SubFactory(
        CloudProviderFactory,
        name="openstack",
    )
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = CloudProject
        django_get_or_create = ["project_id"]


class CloudHostFactory(DjangoModelFactory):
    cloudflavor = factory.SubFactory(CloudFlavorFactory)
    cloudprovider = factory.SubFactory(
        CloudProviderFactory,
        name="openstack",
    )
    host_id = factory.Sequence(lambda n: f"host_id1{n}.local")
    parent = factory.SubFactory(CloudProjectFactory)
    configuration_path = factory.SubFactory(ConfigurationClassFactory)
    service_env = factory.SubFactory(ServiceEnvironmentFactory)

    class Meta:
        model = CloudHost
        django_get_or_create = ["host_id"]


class CloudHostFullFactory(CloudHostFactory):
    hypervisor = factory.SubFactory(DataCenterAssetFactory)
    securityscan = factory.RelatedFactory(SecurityScanFactory, "base_object")

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add("abc, cde", "xyz")


class VirtualServerTypeFactory(DjangoModelFactory):
    name = factory.Iterator(["XEN", "VMWare", "Hyper-V", "Proxmox", "VirtualBox"])

    class Meta:
        model = VirtualServerType
        django_get_or_create = ["name"]


class VirtualServerFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)
    hostname = factory.Sequence(lambda n: "s{0:03d}.local".format(n))
    type = factory.SubFactory(VirtualServerTypeFactory)
    sn = factory.Faker("ssn")
    parent = factory.SubFactory(DataCenterAssetFactory)
    configuration_path = factory.SubFactory(ConfigurationClassFactory)

    class Meta:
        model = VirtualServer


class VirtualServerFullFactory(VirtualServerFactory):
    eth1 = factory.RelatedFactory(EthernetFactory, "base_object")
    eth2 = factory.RelatedFactory(
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
    mem1 = factory.RelatedFactory(MemoryFactory, "base_object")
    mem2 = factory.RelatedFactory(MemoryFactory, "base_object")
    proc1 = factory.RelatedFactory(ProcessorFactory, "base_object")
    proc2 = factory.RelatedFactory(ProcessorFactory, "base_object")
    disk1 = factory.RelatedFactory(DiskFactory, "base_object")
    disk2 = factory.RelatedFactory(DiskFactory, "base_object")
    securityscan = factory.RelatedFactory(SecurityScanFactory, "base_object")

    @factory.post_generation
    def post_tags(self, create, extracted, **kwargs):
        self.tags.add("abc, cde", "xyz")
