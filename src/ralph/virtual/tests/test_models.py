from ddt import data, ddt, unpack

from ralph.assets.models.assets import ServiceEnvironment
from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import EnvironmentFactory, ServiceFactory
from ralph.tests import RalphTestCase
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualComponent
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

        self.cloud_provider = CloudProvider.objects.create(name='openstack')
        self.cloud_flavor = CloudFlavor.objects.create(
            name='flavor_1',
            flavor_id='flavor_id_1',
            cloudprovider=self.cloud_provider,
        )

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

        project1 = CloudProject.objects.create(
            name='project1',
            cloudprovider=self.cloud_provider,
            project_id='project_id_1',
            service_env=self.service_env[1],
        )

        CloudHost.objects.create(
            host_id='host_id1',
            hostname='host1',
            parent=project1,
            cloudflavor=self.cloud_flavor
        )

    @unpack
    @data(
        ('cores', 4),
        ('memory', 1024),
        ('disk', 4096),
    )
    def test_check_cloudflavor_components(self, field, value):
        """check if property cores is correctly returned"""
        flavor = CloudFlavor.objects.get(flavor_id='flavor_id_1')
        self.assertEqual(getattr(flavor, field), value)

    def test_check_project_service_env_inheritance(self):
        """
        Check if CloudHost inherits the service_env variable from its
        parent
        """
        # on project service_env update
        project1 = CloudProject.objects.get(name='project1')
        project1.service_env = self.service_env[0]
        project1.save()
        host1 = CloudHost.objects.get(hostname='host1')
        self.assertEqual(host1.service_env, self.service_env[0])

        # on new host creation
        host2 = CloudHost.objects.create(
            host_id='host_id2',
            hostname='host2',
            parent=project1,
            cloudflavor=self.cloud_flavor
        )
        self.assertEqual(host2.service_env, self.service_env[0])
