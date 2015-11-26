# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from ralph.assets.models.choices import ComponentType
from ralph.assets.models.components import ComponentModel
from ralph.data_center.models.networks import IPAddress
from ralph.tests import RalphTestCase
from ralph.virtual.management.commands.openstack_sync import Command
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualComponent
)
from ralph.virtual.tests.samples.openstack_data import (
    OPENSTACK_DATA,
    OPENSTACK_FLAVOR,
    TEST_HOSTS
)


class OpenstackSyncTestCase(RalphTestCase):

    def setUp(self):
        self.cloud_provider = CloudProvider.objects.create(name='openstack')
        self.cloud_flavor = CloudFlavor.objects.create(
            name='flavor_1',
            flavor_id='flavor_id_1',
            cloudprovider=self.cloud_provider
        )
        self.test_model = ComponentModel(name='delete_test')
        VirtualComponent(model=self.test_model, base_object=self.cloud_flavor)

        self.cloud_flavor = CloudFlavor.objects.create(
            name='flavor_2',
            flavor_id='flavor_id_2',
            cloudprovider=self.cloud_provider
        )
        project1 = CloudProject.objects.create(
            name='project1',
            cloudprovider=self.cloud_provider,
            project_id='project_id_1',
        )
        CloudProject.objects.create(
            name='project2',
            cloudprovider=self.cloud_provider,
            project_id='project_id_2',
        )
        CloudProject.objects.create(
            name='project3',
            cloudprovider=self.cloud_provider,
            project_id='project_os_id1',
        )

        host = CloudHost.objects.create(
            host_id='host_id1',
            hostname='host1',
            parent=project1,
            cloudflavor=self.cloud_flavor
        )
        host.ipaddress_set.create(address='2.2.3.4')

        IPAddress.objects.create(address='1.2.3.4')

        self.cmd = Command()
        self.cmd._get_cloud_provider()
        self.cmd.openstack_projects = OPENSTACK_DATA
        self.cmd.openstack_flavors = OPENSTACK_FLAVOR
        self.cmd._get_ralph_data()

    def test_check_get_ralph_data(self):
        ralph = self.cmd.ralph_projects
        self.assertEqual(ralph['project_id_1']['name'], 'project1')
        self.assertEqual(ralph['project_id_1']['cloudprovider'],
                         self.cloud_provider)

    def test_check_add_ip(self):
        """Check if IP is added correctly to a host"""
        host = CloudHost.objects.get(host_id="host_id1")
        self.cmd._add_ip(host, '9.9.9.9', False)
        ips = map(lambda x: x.address, host.ipaddress_set.all())
        self.assertIn('9.9.9.9', list(ips))

    def test_check_add_ip_assign(self):
        """Check if IP is assigned correctly to a host"""
        host = CloudHost.objects.get(host_id="host_id1")
        self.cmd._add_ip(host, '1.2.3.4', False)
        ips = map(lambda x: x.address, host.ipaddress_set.all())
        self.assertIn('1.2.3.4', list(ips))

    def test_check_add_servers(self):
        """Check if servers are added and modified correctly"""
        project = CloudProject.objects.get(project_id='project_id_1')
        self.cmd._add_servers(TEST_HOSTS, project)

        for host_id in TEST_HOSTS.keys():
            host = CloudHost.objects.get(host_id=host_id)
            ips = map(lambda x: x.address, host.ipaddress_set.all())
            self.assertEqual(host.hostname, TEST_HOSTS[host_id]['hostname'])
            self.assertIn(TEST_HOSTS[host_id]['tag'], host.tags.names())
            for ip in TEST_HOSTS[host_id]['ips']:
                self.assertIn(ip, list(ips))

            # check the creation date only for new hosts
            if host_id.find('_os_') != -1:
                self.assertEqual(
                    datetime.strptime(
                        TEST_HOSTS[host_id]['created'],
                        self.cmd.DATETIME_FORMAT
                    ),
                    host.created,
                )

    def test_check_add_flavor(self):
        """Check if flavors are added and modified correctly"""
        for flavor_id, flavor in OPENSTACK_FLAVOR.items():
            self.cmd._add_flavor(flavor, flavor_id)
            ralph_flavor = CloudFlavor.objects.get(flavor_id=flavor_id)
            self.assertEqual(ralph_flavor.name, flavor['name'])
            self.assertEqual(ralph_flavor.cloudprovider, self.cloud_provider)

    def test_check_process_components(self):
        """Check if components are added and modified correctly"""
        flavor = OPENSTACK_FLAVOR['flavor_id_1']
        flavor_obj = CloudFlavor.objects.get(flavor_id="flavor_id_1")
        self.cmd._process_components(flavor, flavor_obj)

        # cpu
        cpu_name = "{} cores vCPU".format(flavor['cores'])
        model = ComponentModel.objects.get(name=cpu_name)
        self.assertEqual(model.cores, flavor['cores'])
        self.assertEqual(model.type, ComponentType.processor)
        VirtualComponent.objects.get(base_object=flavor_obj, model=model)

        # memory
        mem_name = "{} MiB vMEM".format(flavor['ram'])
        model = ComponentModel.objects.get(name=mem_name)
        self.assertEqual(model.size, flavor['ram'])
        self.assertEqual(model.type, ComponentType.memory)
        VirtualComponent.objects.get(base_object=flavor_obj, model=model)

        # disk
        disk_name = "{} GiB vHDD".format(flavor['disk'])
        model = ComponentModel.objects.get(name=disk_name)
        self.assertEqual(model.size, flavor['disk']*1024)
        self.assertEqual(model.type, ComponentType.disk)
        VirtualComponent.objects.get(base_object=flavor_obj, model=model)

        # delete component
        self.assertRaises(
            ObjectDoesNotExist,
            VirtualComponent.objects.get,
            base_object=flavor_obj, model=self.test_model
        )

    def test_check_complete(self):
        """Check the whole run of the script"""
        self.cmd._update_ralph()
        self.cmd._cleanup()

        # Objects add/modification
        for flavor_id, flavor in OPENSTACK_FLAVOR.items():
            ralph_flavor = CloudFlavor.objects.get(flavor_id=flavor_id)
            self.assertEqual(ralph_flavor.name, flavor['name'])
            self.assertEqual(ralph_flavor.cloudprovider, self.cloud_provider)

        for project_id, project in OPENSTACK_DATA.items():
            ralph_project = CloudProject.objects.get(project_id=project_id)
            self.assertEqual(project['name'], ralph_project.name)
            self.assertEqual(self.cloud_provider, ralph_project.cloudprovider)
            for host_id, host in OPENSTACK_DATA[project_id]['servers'].items():
                ralph_host = CloudHost.objects.get(host_id=host_id)
                ips = map(lambda x: x.address, ralph_host.ipaddress_set.all())
                self.assertEqual(ralph_host.hostname, host['hostname'])
                self.assertIn(host['tag'], ralph_host.tags.names())
                self.assertEqual(set(host['ips']), set(ips))

        # projects removal
        for project_id in ['project_id_2', 'project_id_3']:
            self.assertRaises(
                ObjectDoesNotExist,
                CloudProject.objects.get,
                project_id=project_id,
            )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudFlavor.objects.get,
            flavor_id='flavor_id_2',
        )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudHost.objects.get,
            host_id='host_id1',
        )
        ip = IPAddress.objects.get(address='2.2.3.4')
        self.assertEqual(ip.base_object, None)
