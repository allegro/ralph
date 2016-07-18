from ddt import data, ddt, unpack
from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.assets.models.assets import ServiceEnvironment
from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import (
    EnvironmentFactory,
    EthernetFactory,
    ServiceFactory
)
from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFactory
)
from ralph.networks.tests.factories import IPAddressFactory
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualComponent,
    VirtualServer,
    VirtualServerType
)
from ralph.virtual.tests.factories import (
    CloudFlavorFactory,
    CloudHostFactory,
    CloudProjectFactory,
    CloudProviderFactory,
    VirtualServerFullFactory
)


@ddt
class OpenstackModelsTestCase(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.envs = EnvironmentFactory.create_batch(2)
        self.services = ServiceFactory.create_batch(2)
        self.service_env = []
        for i in range(0, 2):
            self.service_env.append(ServiceEnvironment.objects.create(
                service=self.services[i], environment=self.envs[i]
            ))
        self.service_env[0].service.business_owners = [self.user1]
        self.service_env[0].service.technical_owners = [self.user2]
        self.service_env[0].save()
        self.cloud_provider = CloudProviderFactory(name='openstack')
        self.cloud_flavor = CloudFlavorFactory()
        self.cloud_project = CloudProjectFactory(
            service_env=self.service_env[0]
        )
        self.cloud_host = CloudHostFactory(
            parent=self.cloud_project,
            cloudflavor=self.cloud_flavor
        )

        self.test_cpu = ComponentModel.objects.create(
            name='vcpu1',
            cores=5,
            family='vCPU',
            type=ComponentType.processor,
        )
        self.test_mem = ComponentModel.objects.create(
            name='2000 MiB vMEM',
            size='2000',
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

    @data('cloudflavor', 'cloudhost', 'cloudproject', 'cloudprovider')
    def test_get_list(self, field):
        url = reverse(field + '-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unpack
    @data(
        ('cores', 5),
        ('memory', 2000),
        ('disk', 4096),
    )
    def test_get_cloudflavor_detail(self, field, value):
        url = reverse('cloudflavor-detail', args=(self.cloud_flavor.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[field], value)

    def test_get_cloudhost_detail(self):
        url = reverse('cloudhost-detail', args=(self.cloud_host.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['host_id'], self.cloud_host.host_id)
        self.assertEqual(response.data['hostname'], self.cloud_host.hostname)
        self.assertEqual(response.data['service_env']['id'],
                         self.cloud_host.service_env.id)
        self.assertEqual(response.data['parent']['name'],
                         self.cloud_project.name)
        self.assertEqual(response.data['cloudflavor']['cores'],
                         self.cloud_flavor.cores)
        self.assertEqual(response.data['cloudflavor']['memory'],
                         self.cloud_flavor.memory)
        self.assertEqual(response.data['cloudflavor']['disk'],
                         self.cloud_flavor.disk)
        self.assertEqual(response.data['cloudflavor']['name'],
                         self.cloud_flavor.name)
        self.assertEqual(
            response.data['business_owners'][0]['username'], 'user1'
        )
        self.assertEqual(
            response.data['technical_owners'][0]['username'], 'user2'
        )

    def test_get_cloudproject_detail(self):
        url = reverse('cloudproject-detail', args=(self.cloud_project.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'],
                         self.cloud_project.id)
        self.assertEqual(response.data['name'],
                         self.cloud_project.name)
        self.assertEqual(response.data['service_env']['id'],
                         self.cloud_project.service_env.id)

    def test_get_cloudprovider_detail(self):
        url = reverse('cloudprovider-detail', args=(self.cloud_provider.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.cloud_provider.name)

    def test_create_cloudhost(self):
        url = reverse('cloudhost-list')
        args = {
            'cloudprovider': self.cloud_provider.id,
            'host_id': 'id_1',
            'hostname': 'name_1',
            'parent': self.cloud_project.id,
            'ip_addresses': ['10.0.0.1', '10.0.0.2'],
            'cloudflavor': self.cloud_flavor.id,
            'tags': ['prod', 'db'],
        }
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        host = CloudHost.objects.get(host_id=args['host_id'])
        self.assertEqual(host.cloudprovider, self.cloud_provider)
        self.assertEqual(host.host_id, args['host_id'])
        self.assertEqual(host.hostname, args['hostname'])
        self.assertEqual(host.parent.id, self.cloud_project.id)
        self.assertEqual(host.cloudflavor, self.cloud_flavor)
        self.assertEqual(set(host.tags.names()), set(args['tags']))
        self.assertEqual(host.service_env, self.service_env[0])
        self.assertEqual(set(host.ip_addresses), set(args['ip_addresses']))

    def test_create_cloudflavor(self):
        url = reverse('cloudflavor-list')
        args = {
            'flavor_id': 'id1',
            'name': 'name_2',
            'cores': 4,
            'memory': 1024,
            'disk': 10240,
            'tags': ['prod', 'db'],
            'cloudprovider': self.cloud_provider.id,
        }
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        flavor = CloudFlavor.objects.get(name=args['name'])
        self.assertEqual(flavor.cloudprovider, self.cloud_provider)
        self.assertEqual(flavor.flavor_id, args['flavor_id'])
        self.assertEqual(flavor.name, args['name'])
        self.assertEqual(flavor.cores, args['cores'])
        self.assertEqual(flavor.memory, args['memory'])
        self.assertEqual(flavor.disk, args['disk'])
        self.assertEqual(set(flavor.tags.names()), set(args['tags']))

    def test_create_cloudproject(self):
        url = reverse('cloudproject-list')
        args = {
            'cloudprovider': self.cloud_provider.id,
            'project_id': 'id_1',
            'name': 'name_1',
            'service_env': self.service_env[0].id,
            'tags': ['prod', 'db'],
        }
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = CloudProject.objects.get(project_id=args['project_id'])
        self.assertEqual(project.cloudprovider, self.cloud_provider)
        self.assertEqual(project.project_id, args['project_id'])
        self.assertEqual(project.name, args['name'])
        self.assertEqual(set(project.tags.names()), set(args['tags']))
        self.assertEqual(project.service_env, self.service_env[0])

    def test_create_cloudprovider(self):
        url = reverse('cloudprovider-list')
        args = {'name': 'test1'}
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        provider = CloudProvider.objects.get(name=args['name'])
        self.assertEqual(provider.name, args['name'])

    def test_patch_cloudhost(self):
        url = reverse('cloudhost-detail', args=(self.cloud_host.id,))
        args = {
            'cloudprovider': self.cloud_provider.id,
            'host_id': 'id_1',
            'hostname': 'name_1',
            'parent': self.cloud_project.id,
            'ip_addresses': ['10.0.0.1', '10.0.0.2'],
            'cloudflavor': self.cloud_flavor.id,
            'tags': ['prod', 'db'],
        }
        response = self.client.patch(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        host = CloudHost.objects.get(host_id=args['host_id'])
        self.assertEqual(host.cloudprovider, self.cloud_provider)
        self.assertEqual(host.host_id, args['host_id'])
        self.assertEqual(host.hostname, args['hostname'])
        self.assertEqual(host.parent.id, self.cloud_project.id)
        self.assertEqual(host.cloudflavor, self.cloud_flavor)
        self.assertEqual(set(host.tags.names()), set(args['tags']))
        self.assertEqual(set(host.ip_addresses), set(args['ip_addresses']))

    def test_patch_cloudflavor(self):
        url = reverse('cloudflavor-detail', args=(self.cloud_flavor.id,))
        args = {
            'flavor_id': 'id1',
            'name': 'name_2',
            'cores': 4,
            'memory': 1024,
            'disk': 10240,
            'tags': ['prod', 'db'],
            'cloudprovider': self.cloud_provider.id,
        }
        response = self.client.patch(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flavor = CloudFlavor.objects.get(name=args['name'])
        self.assertEqual(flavor.cloudprovider, self.cloud_provider)
        self.assertEqual(flavor.flavor_id, args['flavor_id'])
        self.assertEqual(flavor.name, args['name'])
        self.assertEqual(flavor.cores, args['cores'])
        self.assertEqual(flavor.memory, args['memory'])
        self.assertEqual(flavor.disk, args['disk'])
        self.assertEqual(set(flavor.tags.names()), set(args['tags']))

    def test_patch_cloudproject(self):
        url = reverse('cloudproject-detail', args=(self.cloud_project.id,))
        args = {
            'cloudprovider': self.cloud_provider.id,
            'project_id': 'id_1',
            'name': 'name_1',
            'service_env': self.service_env[1].id,
            'tags': ['prod', 'db'],
        }
        response = self.client.patch(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = CloudProject.objects.get(project_id=args['project_id'])
        self.assertEqual(project.cloudprovider, self.cloud_provider)
        self.assertEqual(project.project_id, args['project_id'])
        self.assertEqual(project.name, args['name'])
        self.assertEqual(set(project.tags.names()), set(args['tags']))
        self.assertEqual(project.service_env, self.service_env[1])

    def test_patch_cloudprovider(self):
        url = reverse('cloudprovider-detail', args=(self.cloud_provider.id,))
        args = {'name': 'test1'}
        response = self.client.patch(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        provider = CloudProvider.objects.get(name=args['name'])
        self.assertEqual(provider.name, args['name'])

    def test_inheritance_of_service_env_on_change_in_a_cloud_project(self):
        url = reverse('cloudproject-detail', args=(self.cloud_project.id,))
        args = {
            'service_env': self.service_env[1].id,
        }
        response = self.client.patch(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        host = CloudHost.objects.get(host_id=self.cloud_host.host_id)
        self.assertEqual(host.service_env, self.service_env[1])


class VirtualServerAPITestCase(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.hypervisor = DataCenterAssetFactory()
        self.cluster = ClusterFactory()
        self.type = VirtualServerType.objects.create(name='XEN')
        self.virtual_server = VirtualServerFullFactory()
        self.virtual_server.service_env.service.business_owners = [self.user1]
        self.virtual_server.service_env.service.technical_owners = [self.user2]
        self.virtual_server.service_env.save()
        self.virtual_server2 = VirtualServerFullFactory()
        self.ip = IPAddressFactory(
            ethernet=EthernetFactory(base_object=self.virtual_server2)
        )

    def test_get_virtual_server_list(self):
        url = reverse('virtualserver-list')
        with self.assertNumQueries(13):
            response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_get_virtual_server_details(self):
        url = reverse('virtualserver-detail', args=(self.virtual_server.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['hostname'],
            self.virtual_server.hostname
        )
        self.assertEqual(len(response.data['ethernet']), 2)
        self.assertCountEqual(
            [
                eth['ipaddress']['address']
                for eth in response.data['ethernet']
                if eth['ipaddress']
            ],
            self.virtual_server.ipaddresses.values_list('address', flat=True)
        )
        self.assertEqual(len(response.data['memory']), 2)
        self.assertEqual(response.data['memory'][0]['speed'], 1600)
        self.assertEqual(response.data['memory'][0]['size'], 8192)
        self.assertEqual(
            response.data['business_owners'][0]['username'], 'user1'
        )
        self.assertEqual(
            response.data['technical_owners'][0]['username'], 'user2'
        )

    def test_create_virtual_server(self):
        virtual_server_count = VirtualServer.objects.count()
        url = reverse('virtualserver-list')
        data = {
            'hostname': 's1234.local',
            'type': self.type.id,
            'sn': '143ed36a-3e86-457d-9e19-3dcfe4d5ed26',
            'hypervisor': self.hypervisor.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            VirtualServer.objects.count(), virtual_server_count + 1
        )
        virtual_server = VirtualServer.objects.get(pk=response.data['id'])
        self.assertEqual(virtual_server.hostname, data['hostname'])
        self.assertEqual(virtual_server.parent.id, self.hypervisor.id)
        self.assertEqual(virtual_server.sn, data['sn'])

    def test_patch_virtual_server(self):
        url = reverse('virtualserver-detail', args=(self.virtual_server.id,))
        data = {
            'hostname': 's111111.local'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.virtual_server.refresh_from_db()
        self.assertEqual(self.virtual_server.hostname, 's111111.local')

    def test_filter_by_configuration_path(self):
        url = reverse('virtualserver-list') + '?configuration_path={}'.format(
            self.virtual_server.configuration_path.path,
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_hostname(self):
        url = reverse('virtualserver-list') + '?hostname={}'.format(
            self.virtual_server.hostname,
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_ip_address(self):
        url = reverse('virtualserver-list') + '?ip={}'.format(
            self.ip.address,
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_service_uid(self):
        url = reverse('virtualserver-list') + '?service={}'.format(
            self.virtual_server.service_env.service.uid,
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_service_uid2(self):
        url = (
            reverse('virtualserver-list') +
            '?service_env__service__uid={}'.format(
                self.virtual_server.service_env.service.uid,
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_service_id(self):
        url = (
            reverse('virtualserver-list') +
            '?service_env__service__id={}'.format(
                self.virtual_server.service_env.service.id,
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_service_name(self):
        url = reverse('virtualserver-list') + '?service={}'.format(
            self.virtual_server.service_env.service.name,
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )

    def test_filter_by_service_name2(self):
        url = (
            reverse('virtualserver-list') +
            '?service_env__service__name={}'.format(
                self.virtual_server.service_env.service.name,
            )
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['count'], 1
        )
