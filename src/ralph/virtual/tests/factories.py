import factory
from factory.django import DjangoModelFactory

from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualServer,
    VirtualServerType
)


class CloudProviderFactory(DjangoModelFactory):

    class Meta:
        model = CloudProvider
        django_get_or_create = ['name']


class CloudFlavorFactory(DjangoModelFactory):

    name = factory.Iterator(['flavor1', 'flavor2', 'flavor3'])
    flavor_id = factory.Iterator(['flavor_id1', 'flavor_id2', 'flavor_id3'])
    cloudprovider = factory.SubFactory(
        CloudProviderFactory,
        name='openstack'
    )

    class Meta:
        model = CloudFlavor
        django_get_or_create = ['flavor_id']


class CloudProjectFactory(DjangoModelFactory):

    name = factory.Iterator(['project1', 'project2', 'project3'])
    project_id = factory.Iterator(
        ['project_id1', 'project_id2', 'project_id3']
    )
    cloudprovider = factory.SubFactory(
        CloudProviderFactory,
        name='openstack',
    )

    class Meta:
        model = CloudProject
        django_get_or_create = ['project_id']


class CloudHostFactory(DjangoModelFactory):

    cloudflavor = factory.SubFactory(CloudFlavorFactory)
    cloudprovider = factory.SubFactory(
        CloudProviderFactory,
        name='openstack',
    )
    host_id = factory.Iterator(['host_id1', 'host_id2', 'host_id3'])
    parent = factory.SubFactory(CloudProjectFactory)

    class Meta:
        model = CloudHost
        django_get_or_create = ['host_id']


class VirtualServerTypeFactory(DjangoModelFactory):
    name = factory.Iterator(
        ['XEN', 'VMWare', 'Hyper-V', 'Proxmox', 'VirtualBox']
    )

    class Meta:
        model = VirtualServerType
        django_get_or_create = ['name']


class VirtualServerFactory(DjangoModelFactory):
    service_env = factory.SubFactory(ServiceEnvironmentFactory)
    hostname = factory.Sequence(lambda n: 's{0:03d}.local'.format(n))
    type = factory.SubFactory(VirtualServerTypeFactory)
    sn = factory.Faker('ssn')
    parent = factory.SubFactory(DataCenterAssetFactory)

    class Meta:
        model = VirtualServer
