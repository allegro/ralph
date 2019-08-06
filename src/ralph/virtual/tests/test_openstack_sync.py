# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings

from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import DataCenterAssetModelFactory
from ralph.data_center.models.physical import DataCenterAsset
from ralph.networks.models.networks import IPAddress
from ralph.tests import RalphTestCase
from ralph.virtual.management.commands.openstack_sync import Command
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
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


class FakeIronicNode(object):
    def __init__(self, serial_number, instance_uuid):
        self.extra = {'serial_number': serial_number}
        self.instance_uuid = instance_uuid


class TestOpenstackSync(RalphTestCase):

    def setUp(self):
        asset_model = DataCenterAssetModelFactory()
        self.cloud_provider = CloudProviderFactory(name='openstack')
        self.cloud_flavor = CloudFlavorFactory.create_batch(3)
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
        IPAddress.objects.create(base_object=host, address='2.2.3.4')
        IPAddress.objects.create(base_object=host, address='1.2.3.4')

        DataCenterAsset.objects.create(
            hostname='hypervisor_os1.dcn.net',
            model=asset_model,
        )

        self.cmd = Command()
        self.cmd._get_cloud_provider()
        self.cmd.openstack_projects = OPENSTACK_DATA
        self.cmd.openstack_flavors = OPENSTACK_FLAVOR
        self.cmd._get_ralph_data()
        self.cmd.ironic_serial_number_param = 'serial_number'
        self.cmd.ralph_serial_number_param = 'sn'

    def test_check_get_ralph_data(self):
        ralph = self.cmd.ralph_projects
        self.assertEqual(ralph['project_id1']['name'], self.cloud_project.name)

    def test_check_process_servers(self):
        """Check if servers are added and modified correctly"""
        self.cmd._process_servers(TEST_HOSTS, self.cloud_project)

        for host_id, test_host in TEST_HOSTS.items():
            host = CloudHost.objects.get(host_id=host_id)
            ips = host.ip_addresses
            self.assertEqual(host.hostname, test_host['hostname'])
            self.assertIn(test_host['tag'], host.tags.names())
            self.assertEqual(self.cloud_provider, host.cloudprovider)
            for ip in test_host['ips']:
                self.assertIn(ip, list(ips))
            self.assertEqual(host.hypervisor.hostname, test_host['hypervisor'])

            # check the creation date only for new hosts
            if host_id.find('_os_') != -1:
                self.assertEqual(
                    datetime.strptime(
                        test_host['created'],
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
                ips = ralph_host.ip_addresses
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

    def test_cleanup_doesnt_remove_cloud_projects_with_children(self):
        project = CloudProjectFactory(project_id='im_not_here')
        host = CloudHostFactory(
            host_id='host_id123',
            parent=project,
            cloudflavor=self.cloud_flavor[1]
        )
        self.cmd._get_ralph_data()

        self.cmd._cleanup()

        try:
            CloudProject.objects.get(project_id='im_not_here')
        except ObjectDoesNotExist:
            self.fail('Project "im_not_here" was deleted.')

    def test_delete_cloud_instance_cleanup_ip(self):
        ips_count = IPAddress.objects.count()
        self.cmd._cleanup_servers({}, self.cloud_project.project_id)
        # cloud instance in cloud_project had 2 ip addresses
        self.assertEqual(IPAddress.objects.count(), ips_count - 2)

    @override_settings(OPENSTACK_INSTANCES=[
        {
            'username': 'root',
            'password': 'root',
            'tenant_name': 'admin',
            'version': '2.0',
            'auth_url': 'http://10.20.30.41:1111/v2.0/',
            'tag': 'my_os',
            'network_regex': '.*',
        },
        {
            'username': 'root',
            'password': 'root',
            'tenant_name': 'admin2',
            'version': '2.0',
            'auth_url': 'http://10.20.30.42:1111/v2.0/',
            'tag': 'my_os_2',
            'network_regex': '.*',
            'provider': 'openstack',
        },
        {
            'username': 'root',
            'password': 'root',
            'tenant_name': 'admin3',
            'version': '2.0',
            'auth_url': 'http://10.20.30.43:1111/v2.0/',
            'tag': 'my_os_3',
            'network_regex': '.*',
            'provider': 'my-own-openstack'
        },
    ])
    def test_non_default_provider(self):
        tenants = [
            os['tenant_name'] for os in self.cmd._get_instances_from_settings()
        ]
        self.assertCountEqual(tenants, ['admin', 'admin2'])
        self.cmd.openstack_provider_name = 'my-own-openstack'
        self.cmd._get_cloud_provider()
        self.assertTrue(
            CloudProvider.objects.filter(name='my-own-openstack').exists()
        )
        tenants = [
            os['tenant_name'] for os in self.cmd._get_instances_from_settings()
        ]
        self.assertCountEqual(tenants, ['admin3'])

    def test_match_cloud_hosts_all_matched(self):
        asset_model = DataCenterAssetModelFactory()
        num_assets = 10

        assets = [
            DataCenterAsset.objects.create(
                hostname='hostname-{}'.format(i),
                model=asset_model,
                sn='SN{}'.format(i)
            )
            for i in range(num_assets)
        ]
        hosts = [
            CloudHostFactory(host_id='fake-instance-uuid-{}'.format(i))
            for i in range(num_assets)
        ]

        nodes = [
            FakeIronicNode(serial_number=asset.sn, instance_uuid=host.host_id)
            for asset, host in zip(assets, hosts)
        ]

        self.cmd._match_nodes_to_hosts(nodes)

        updated_hosts = CloudHost.objects.filter(
            id__in=[host.id for host in hosts]
        )

        for host in updated_hosts:
            self.assertIsNotNone(host.hypervisor)

        expected_serials = [asset.sn for asset in assets]
        expected_serials.sort()

        real_serials = [host.hypervisor.sn for host in updated_hosts]
        real_serials.sort()

        self.assertEqual(expected_serials, real_serials)

    def test_match_cloud_hosts_host_not_found(self):
        host = CloudHostFactory(host_id='foo')
        node = FakeIronicNode(serial_number='SN0', instance_uuid='bar')
        self.cmd._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)

    def test_match_cloud_hosts_asset_not_found(self):
        asset_model = DataCenterAssetModelFactory()
        DataCenterAsset.objects.create(
            hostname='hostname-1',
            model=asset_model,
            sn='FOO'
        )

        host = CloudHostFactory(host_id='buz')
        node = FakeIronicNode(serial_number='BAR', instance_uuid=host.host_id)
        self.cmd._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)

    def test_match_cloud_hosts_asset_duplicate_sn(self):
        asset_model = DataCenterAssetModelFactory()
        assets = [
            DataCenterAsset.objects.create(
                hostname='hostname-{}'.format(i),
                model=asset_model,
                sn=None
            )
            for i in range(2)
        ]

        host = CloudHostFactory(host_id='bar')
        node = FakeIronicNode(
            serial_number=assets[0].sn,
            instance_uuid=host.host_id
        )

        self.cmd._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)
