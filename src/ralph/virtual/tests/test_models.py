from ddt import data, ddt, unpack

from ralph.assets.models.assets import ServiceEnvironment
from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import EnvironmentFactory, ServiceFactory
from ralph.tests import RalphTestCase
from ralph.virtual.models import CloudHost, VirtualComponent
from ralph.virtual.tests.factories import (
    CloudFlavorFactory,
    CloudHostFactory,
    CloudProjectFactory,
    CloudProviderFactory
)


@ddt
class OpenstackModelsTestCase(RalphTestCase):
    def setUp(self):
        self.envs = EnvironmentFactory.create_batch(2)
        self.services = ServiceFactory.create_batch(2)
        self.service_env = []
        for i in range(0, 2):
            self.service_env.append(ServiceEnvironment.objects.create(
                service=self.services[i], environment=self.envs[i]
            ))

        self.cloud_provider = CloudProviderFactory(name='openstack')
        self.cloud_flavor = CloudFlavorFactory()
        self.cloud_project = CloudProjectFactory()
        self.cloud_host = CloudHostFactory(parent=self.cloud_project)

        self.test_cpu = ComponentModel.objects.create(
            name='vcpu1',
            cores=4,
            family='vCPU',
            type=ComponentType.processor,
        )
        self.test_mem = ComponentModel.objects.create(
            name='1024 MiB vMEM',
            size='1024',
            type=ComponentType.memory,
        )
        self.test_disk = ComponentModel.objects.create(
            name='4 GiB vDISK',
            size='4096',
            type=ComponentType.disk,
        )

        VirtualComponent.objects.create(
            base_object=self.cloud_flavor,
            model=self.test_cpu,
        )
        VirtualComponent.objects.create(
            base_object=self.cloud_flavor,
            model=self.test_mem,
        )
        VirtualComponent.objects.create(
            base_object=self.cloud_flavor,
            model=self.test_disk,
        )

    @unpack
    @data(
        ('cores', 4),
        ('memory', 1024),
        ('disk', 4096),
    )
    def test_cloudflavor_get_components(self, field, value):
        self.assertEqual(getattr(self.cloud_flavor, field), value)

    @unpack
    @data(
        ('cores', 8),
        ('memory', 2048),
        ('disk', 1024),
    )
    def test_cloudflavor_set_components(self, key, value):
        setattr(self.cloud_flavor, key, value)
        self.assertEqual(getattr(self.cloud_flavor, key), value)

    def test_check_cloudhost_ip_addresses_setter(self):
        ip_addresses = ['10.0.0.1', '10.0.0.2']
        ip_addresses2 = ['10.31.0.1', '10.30.0.0']
        self.cloud_host.ip_addresses = ip_addresses
        self.assertEqual(set(self.cloud_host.ip_addresses), set(ip_addresses))
        self.cloud_host.ip_addresses = ip_addresses2
        self.assertEqual(set(self.cloud_host.ip_addresses), set(ip_addresses2))

    def test_service_env_inheritance_on_project_change(self):
        self.cloud_project.service_env = self.service_env[0]
        self.cloud_project.save()
        updated_host = CloudHost.objects.get(pk=self.cloud_host.id)
        self.assertEqual(updated_host.service_env, self.service_env[0])

    def test_service_env_inheritance_on_host_creation(self):
        self.cloud_project.service_env = self.service_env[1]
        self.cloud_project.save()
        new_host = CloudHostFactory(
            host_id="new_host_id",
            parent=self.cloud_project
        )
        self.assertEqual(new_host.service_env, self.service_env[1])
