# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from dateutil import parser
from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import DataCenterAssetModelFactory
from ralph.data_center.models.networks import IPAddress
from ralph.data_center.models.physical import DataCenterAsset
from ralph.tests import RalphTestCase
from ralph.virtual.management.commands.openstack_sync import Command
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    VirtualComponent
)
from ralph.virtual.tests.factories import (
    CloudFlavorFactory,
    CloudHostFactory,
    CloudProjectFactory,
    CloudProviderFactory
)
from ralph.virtual.tests.samples.openstack_data import (
    OPENSTACK_DATA,
    OPENSTACK_FLAVOR,
    TEST_HOSTS
)


class TestOpenstackSync(RalphTestCase):

    def setUp(self):
        asset_model = DataCenterAssetModelFactory()
        self.cloud_provider = CloudProviderFactory(name='openstack')
        self.cloud_flavor = CloudFlavorFactory.create_batch(2)
        self.test_model = ComponentModel(name='delete_test')
        VirtualComponent(
            model=self.test_model,
            base_object=self.cloud_flavor[0]
        )

        self.cloud_project = CloudProjectFactory(project_id='project_id1')
        CloudProjectFactory(project_id='project_id2')
        CloudProjectFactory(project_id='project_os_id1')

        host = CloudHostFactory(
            host_id='host_id1',
            parent=self.cloud_project,
            cloudflavor=self.cloud_flavor[1]
        )
        host.ipaddress_set.create(address='2.2.3.4')

        IPAddress.objects.create(address='1.2.3.4')

        DataCenterAsset.objects.create(
            hostname='hypervisor_os1.dcn.net',
            model=asset_model,
        )

        self.cmd = Command()
        self.cmd._get_cloud_provider()
        self.cmd.openstack_projects = OPENSTACK_DATA
        self.cmd.openstack_flavors = OPENSTACK_FLAVOR
        self.cmd._get_ralph_data()

    def test_check_get_ralph_data(self):
        ralph = self.cmd.ralph_projects
        self.assertEqual(ralph['project_id1']['name'], self.cloud_project.name)

    def test_check_process_servers(self):
        """Check if servers are added and modified correctly"""
        self.cmd._process_servers(TEST_HOSTS, self.cloud_project)

        for host_id, test_host in TEST_HOSTS.items():
            host = CloudHost.objects.get(host_id=host_id)
            ips = map(lambda x: x.address, host.ipaddress_set.all())
            self.assertEqual(host.hostname, test_host['hostname'])
            self.assertIn(test_host['tag'], host.tags.names())
            self.assertEqual(self.cloud_provider, host.cloudprovider)
            for ip in test_host['ips']:
                self.assertIn(ip, list(ips))
            self.assertEqual(host.hypervisor.hostname, test_host['hypervisor'])

            # check the creation date only for new hosts
            if host_id.find('_os_') != -1:
                self.assertEqual(
                    parser.parse(test_host['created']), host.created,
                )

    def test_check_add_flavor(self):
        """Check if flavors are added and modified correctly"""
        for flavor_id, flavor in OPENSTACK_FLAVOR.items():
            self.cmd._add_flavor(flavor, flavor_id)
            ralph_flavor = CloudFlavor.objects.get(flavor_id=flavor_id)
            self.assertEqual(ralph_flavor.name, flavor['name'])
            self.assertEqual(ralph_flavor.cloudprovider, self.cloud_provider)
            self.assertIn(flavor['tag'], ralph_flavor.tags.names())
            self.assertEqual(flavor['cores'], ralph_flavor.cores)
            self.assertEqual(flavor['memory'], ralph_flavor.memory)
            self.assertEqual(flavor['disk'], ralph_flavor.disk)

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
        for project_id in ['project_id2', 'project_id3']:
            self.assertRaises(
                ObjectDoesNotExist,
                CloudProject.objects.get,
                project_id=project_id,
            )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudFlavor.objects.get,
            flavor_id='flavor_id2',
        )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudHost.objects.get,
            host_id='host_id1',
        )
        ip = IPAddress.objects.get(address='2.2.3.4')
        self.assertEqual(ip.base_object, None)
