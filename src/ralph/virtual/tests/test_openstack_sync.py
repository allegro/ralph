# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime

import mock
from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings

from ralph.assets.models.components import ComponentModel
from ralph.assets.tests.factories import DataCenterAssetModelFactory
from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib.openstack.client import RalphOpenStackInfrastructureClient
from ralph.networks.models.networks import IPAddress
from ralph.tests import RalphTestCase
from ralph.virtual.management.commands.openstack_sync import RalphClient
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
    CloudHostFullFactory,
    CloudProjectFactory,
    CloudProviderFactory
)
from ralph.virtual.tests.samples.openstack_data import (
    OPENSTACK_DATA,
    OPENSTACK_FLAVORS,
    OPENSTACK_INSTANCES
)


class FakeIronicNode(object):
    def __init__(self, serial_number, instance_uuid):
        self.extra = {"serial_number": serial_number}
        self.instance_uuid = instance_uuid


class TestOpenstackSync(RalphTestCase):
    def setUp(self):
        asset_model = DataCenterAssetModelFactory()
        self.cloud_provider = CloudProviderFactory(name="openstack")
        self.cloud_flavor = CloudFlavorFactory.create_batch(3)
        self.test_model = ComponentModel(name="delete_test")
        VirtualComponent(model=self.test_model, base_object=self.cloud_flavor[0])

        self.cloud_project_1 = CloudProjectFactory(project_id="project_id1")
        self.cloud_project_2 = CloudProjectFactory(project_id="project_id2")
        self.cloud_project_3 = CloudProjectFactory(project_id="project_os_id1")

        self.host = CloudHostFactory(
            host_id="host_id1",
            parent=self.cloud_project_1,
            cloudflavor=self.cloud_flavor[1],
        )
        IPAddress.objects.create(base_object=self.host, address="2.2.3.4")
        IPAddress.objects.create(base_object=self.host, address="1.2.3.4")

        DataCenterAsset.objects.create(
            hostname="hypervisor_os1.dcn.net",
            model=asset_model,
        )

        self.ironic_serial_number_param = "serial_number"
        self.ralph_serial_number_param = "sn"
        self.ralph_client = RalphClient(
            "openstack", self.ironic_serial_number_param, self.ralph_serial_number_param
        )
        self.openstack_client = RalphOpenStackInfrastructureClient(
            self.cloud_provider.name
        )

    def test_check_get_ralph_data(self):
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        self.assertEqual(
            ralph_projects["project_id1"]["name"], self.cloud_project_1.name
        )
        self.assertIn("host_id1", ralph_projects["project_id1"]["servers"].keys())

    def test_check_process_servers(self):
        """Check if servers are added and modified correctly"""
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        self.ralph_client._add_or_update_servers(
            OPENSTACK_INSTANCES, self.cloud_project_1.project_id, ralph_projects
        )
        for host_id, test_host in OPENSTACK_INSTANCES.items():
            if test_host["status"] == "DELETED":
                self.assertRaises(
                    ObjectDoesNotExist, CloudHost.objects.get, host_id=host_id
                )
                continue
            host = CloudHost.objects.get(host_id=host_id)
            ips = host.ip_addresses
            self.assertEqual(host.hostname, test_host["hostname"])
            self.assertIn(test_host["tag"], host.tags.names())
            self.assertEqual(self.cloud_provider, host.cloudprovider)
            for ip in test_host["ips"]:
                self.assertIn(ip, list(ips))
            self.assertEqual(host.hypervisor.hostname, test_host["hypervisor"])

            # check the creation date only for new hosts
            if host_id.find("_os_") != -1:
                self.assertEqual(
                    datetime.strptime(
                        test_host["created"], self.ralph_client.DATETIME_FORMAT
                    ),
                    host.created,
                )

    def test_check_add_flavor(self):
        """Check if flavors are added and modified correctly"""
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        for flavor_id, flavor in OPENSTACK_FLAVORS.items():
            self.ralph_client._add_or_modify_flavours(flavor, flavor_id, ralph_flavors)
            ralph_flavor = CloudFlavor.objects.get(flavor_id=flavor_id)
            self.assertEqual(ralph_flavor.name, flavor["name"])
            self.assertEqual(ralph_flavor.cloudprovider, self.cloud_provider)
            self.assertIn(flavor["tag"], ralph_flavor.tags.names())
            self.assertEqual(flavor["cores"], ralph_flavor.cores)
            self.assertEqual(flavor["memory"], ralph_flavor.memory)
            self.assertEqual(flavor["disk"], ralph_flavor.disk)

    def test_check_ralph_update(self):
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavours = self.ralph_client.get_ralph_flavors()
        self.ralph_client.perform_update(
            OPENSTACK_DATA, OPENSTACK_FLAVORS, ralph_projects, ralph_flavours
        )

        # Objects addition/modification
        for flavor_id, flavor in OPENSTACK_FLAVORS.items():
            ralph_flavor = CloudFlavor.objects.get(flavor_id=flavor_id)
            self.assertEqual(ralph_flavor.name, flavor["name"])
            self.assertEqual(ralph_flavor.cloudprovider, self.cloud_provider)

        for project_id, project in OPENSTACK_DATA.items():
            ralph_project = CloudProject.objects.get(project_id=project_id)
            self.assertEqual(project["name"], ralph_project.name)
            self.assertEqual(self.cloud_provider, ralph_project.cloudprovider)
            for host_id, host in OPENSTACK_DATA[project_id]["servers"].items():
                if host["status"] == "DELETED":
                    self.assertRaises(
                        ObjectDoesNotExist, CloudHost.objects.get, host_id=host_id
                    )
                    continue
                ralph_host = CloudHost.objects.get(host_id=host_id)
                ips = ralph_host.ip_addresses
                self.assertEqual(ralph_host.hostname, host["hostname"])
                self.assertIn(host["tag"], ralph_host.tags.names())
                self.assertEqual(set(host["ips"]), set(ips))

    def test_check_ralph_delete(self):
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA,
            ralph_projects,
        )
        self.ralph_client.perform_delete(
            OPENSTACK_DATA,
            OPENSTACK_FLAVORS,
            ralph_projects,
            ralph_flavors,
            servers_to_delete,
        )
        # projects removal
        for project_id in ["project_id2", "project_id3"]:
            self.assertRaises(
                ObjectDoesNotExist,
                CloudProject.objects.get,
                project_id=project_id,
            )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudFlavor.objects.get,
            flavor_id="flavor_id2",
        )
        self.assertRaises(
            ObjectDoesNotExist,
            CloudHost.objects.get,
            host_id="host_id1",
        )

    def test_check_ralph_delete_incremental(self):
        # Create server to be deleted in Ralph
        host_to_delete = CloudHostFactory(
            host_id="deleted",
            parent=self.cloud_project_3,
            cloudflavor=self.cloud_flavor[1],
        )
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA, ralph_projects, incremental=True
        )
        self.ralph_client.perform_delete(
            OPENSTACK_DATA,
            OPENSTACK_FLAVORS,
            ralph_projects,
            ralph_flavors,
            servers_to_delete,
        )
        self.assertRaises(
            ObjectDoesNotExist, CloudHost.objects.get, host_id=host_to_delete.host_id
        )
        try:
            CloudHost.objects.get(host_id=self.host.host_id)
        except ObjectDoesNotExist:
            self.fail("Removed host that should have been kept.")

    def test_cleanup_doesnt_remove_cloud_projects_with_children(self):
        project = CloudProjectFactory(project_id="im_not_here")
        CloudHostFactory(
            host_id="host_id123", parent=project, cloudflavor=self.cloud_flavor[1]
        )
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA,
            ralph_projects,
        )
        self.ralph_client.perform_delete(
            OPENSTACK_DATA,
            OPENSTACK_FLAVORS,
            ralph_projects,
            ralph_flavors,
            servers_to_delete,
        )

        try:
            CloudProject.objects.get(project_id="im_not_here")
        except ObjectDoesNotExist:
            self.fail('Project "im_not_here" was deleted.')

    def test_cleanup_doesnt_remove_cloud_projects_with_different_provider(self):
        CloudProjectFactory(
            project_id="im_not_here",
            cloudprovider=CloudProviderFactory(name="some_random_provider"),
        )
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA,
            ralph_projects,
        )
        self.ralph_client.perform_delete(
            OPENSTACK_DATA,
            OPENSTACK_FLAVORS,
            ralph_projects,
            ralph_flavors,
            servers_to_delete,
        )

        try:
            CloudProject.objects.get(project_id="im_not_here")
        except ObjectDoesNotExist:
            self.fail('Project "im_not_here" was deleted.')

    def test_cleanup_doesnt_remove_cloud_flavours_with_assignments(self):
        flavor = CloudFlavorFactory(flavor_id="im_not_here", name="im_not_here")
        CloudHostFactory(host_id="host_id123", cloudflavor=flavor)
        openstack_flavors = copy(OPENSTACK_FLAVORS)
        openstack_flavors.update({flavor.flavor_id: {"name": flavor.name}})
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA, ralph_projects, incremental=True
        )
        self.ralph_client.perform_delete(
            OPENSTACK_DATA,
            OPENSTACK_FLAVORS,
            ralph_projects,
            ralph_flavors,
            servers_to_delete,
        )

        try:
            CloudFlavor.objects.get(flavor_id="im_not_here")
        except ObjectDoesNotExist:
            self.fail('Flavor "im_not_here" was deleted.')

    def test_delete_cloud_instance_cleanup_ip(self):
        ips_count = IPAddress.objects.count()
        ralph_projects = self.ralph_client.get_ralph_servers_data(
            self.ralph_client.get_ralph_projects()
        )
        servers_to_delete = self.ralph_client.calculate_servers_to_delete(
            OPENSTACK_DATA,
            ralph_projects,
        )
        self.ralph_client._delete_servers(servers_to_delete)
        # cloud instance in cloud_project had 2 ip addresses
        self.assertEqual(IPAddress.objects.count(), ips_count - 2)

    @override_settings(
        OPENSTACK_INSTANCES=[
            {
                "username": "root",
                "password": "root",
                "tenant_name": "admin",
                "version": "2.0",
                "auth_url": "http://10.20.30.41:1111/v2.0/",
                "tag": "my_os",
                "network_regex": ".*",
            },
            {
                "username": "root",
                "password": "root",
                "tenant_name": "admin2",
                "version": "2.0",
                "auth_url": "http://10.20.30.42:1111/v2.0/",
                "tag": "my_os_2",
                "network_regex": ".*",
                "provider": "openstack",
            },
            {
                "username": "root",
                "password": "root",
                "tenant_name": "admin3",
                "version": "2.0",
                "auth_url": "http://10.20.30.43:1111/v2.0/",
                "tag": "my_os_3",
                "network_regex": ".*",
                "provider": "my-own-openstack",
            },
        ]
    )
    @mock.patch(
        "ralph.lib.openstack.client.RalphOpenstackClient._get_nova_client_connection"
    )
    @mock.patch("ralph.lib.openstack.client.RalphOpenstackClient._get_keystone_client")
    def test_non_default_provider(self, get_kc, get_nc):
        tenants = [
            os.site["tenant_name"]
            for os in self.openstack_client._get_instances_from_settings()
        ]
        self.assertCountEqual(tenants, ["admin", "admin2"])

        RalphClient(
            "my-own-openstack",
            self.ironic_serial_number_param,
            self.ralph_serial_number_param,
        )
        new_openstack_client = RalphOpenStackInfrastructureClient(
            "my-own-openstack",
        )
        self.assertTrue(CloudProvider.objects.filter(name="my-own-openstack").exists())
        tenants = [
            os.site["tenant_name"]
            for os in new_openstack_client._get_instances_from_settings()
        ]
        self.assertCountEqual(tenants, ["admin3"])

    def test_match_cloud_hosts_all_matched(self):
        asset_model = DataCenterAssetModelFactory()
        num_assets = 10

        assets = [
            DataCenterAsset.objects.create(
                hostname="hostname-{}".format(i), model=asset_model, sn="SN{}".format(i)
            )
            for i in range(num_assets)
        ]
        hosts = [
            CloudHostFactory(host_id="fake-instance-uuid-{}".format(i))
            for i in range(num_assets)
        ]

        nodes = [
            FakeIronicNode(serial_number=asset.sn, instance_uuid=host.host_id)
            for asset, host in zip(assets, hosts)
        ]

        self.ralph_client._match_nodes_to_hosts(nodes)

        updated_hosts = CloudHost.objects.filter(id__in=[host.id for host in hosts])

        for host in updated_hosts:
            self.assertIsNotNone(host.hypervisor)

        expected_serials = [asset.sn for asset in assets]
        expected_serials.sort()

        real_serials = [host.hypervisor.sn for host in updated_hosts]
        real_serials.sort()

        self.assertEqual(expected_serials, real_serials)

    def test_match_cloud_hosts_ignore_already_matched(self):
        unassigned_hypervisor = DataCenterAsset.objects.create(
            hostname="hypervisor",
            model=DataCenterAssetModelFactory(),
            sn="hypervisor-SN",
        )

        with_hypervisor = CloudHostFullFactory(host_id="with hypervisor")
        with_hypervisor_modified = with_hypervisor.modified
        with_hypervisor_node = FakeIronicNode(
            serial_number=with_hypervisor.hypervisor.sn,
            instance_uuid=with_hypervisor.host_id,
        )

        without_hypervisor = CloudHostFactory(host_id="no hypervisor")
        without_hypervisor_modified = without_hypervisor.modified
        without_hypervisor_node = FakeIronicNode(
            serial_number=unassigned_hypervisor.sn,
            instance_uuid=without_hypervisor.host_id,
        )

        nodes = [with_hypervisor_node, without_hypervisor_node]

        self.ralph_client._match_nodes_to_hosts(nodes)
        without_hypervisor.refresh_from_db()
        with_hypervisor.refresh_from_db()

        # should not be modified by the command
        self.assertTrue(with_hypervisor_modified == with_hypervisor.modified)
        # should be modified by the command
        self.assertTrue(without_hypervisor_modified < without_hypervisor.modified)

    def test_match_cloud_hosts_host_not_found(self):
        host = CloudHostFactory(host_id="foo")
        node = FakeIronicNode(serial_number="SN0", instance_uuid="bar")
        self.ralph_client._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)

    def test_match_cloud_hosts_asset_not_found(self):
        asset_model = DataCenterAssetModelFactory()
        DataCenterAsset.objects.create(
            hostname="hostname-1", model=asset_model, sn="FOO"
        )

        host = CloudHostFactory(host_id="buz")
        node = FakeIronicNode(serial_number="BAR", instance_uuid=host.host_id)
        self.ralph_client._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)

    def test_match_cloud_hosts_asset_duplicate_sn(self):
        asset_model = DataCenterAssetModelFactory()
        assets = [
            DataCenterAsset.objects.create(
                hostname="hostname-{}".format(i), model=asset_model, sn=None
            )
            for i in range(2)
        ]

        host = CloudHostFactory(host_id="bar")
        node = FakeIronicNode(serial_number=assets[0].sn, instance_uuid=host.host_id)

        self.ralph_client._match_nodes_to_hosts([node])

        updated_host = CloudHost.objects.get(pk=host.pk)
        self.assertIsNone(updated_host.hypervisor)

    def test_get_or_create_cloud_provider(self):
        existing_provider = self.ralph_client._get_or_create_cloud_provider("openstack")
        self.assertEqual(self.cloud_provider.name, existing_provider.name)
        new_provider = self.ralph_client._get_or_create_cloud_provider("new_provider")
        self.assertEqual("new_provider", new_provider.name)
        self.assertIsInstance(new_provider, CloudProvider)

    def test_get_ralph_projects(self):
        ralph_projects = self.ralph_client.get_ralph_projects()
        expected_result = {
            self.cloud_project_1.project_id: {
                "name": self.cloud_project_1.name,
                "servers": {},
                "tags": [],
            },
            self.cloud_project_2.project_id: {
                "name": self.cloud_project_2.name,
                "servers": {},
                "tags": [],
            },
            self.cloud_project_3.project_id: {
                "name": self.cloud_project_3.name,
                "servers": {},
                "tags": [],
            },
        }
        self.assertDictEqual(expected_result, ralph_projects)

    def test_get_ralph_flavors(self):
        ralph_flavors = self.ralph_client.get_ralph_flavors()
        expected_flavors = {
            self.cloud_flavor[0].flavor_id: {"name": self.cloud_flavor[0].name},
            self.cloud_flavor[1].flavor_id: {"name": self.cloud_flavor[1].name},
            self.cloud_flavor[2].flavor_id: {"name": self.cloud_flavor[2].name},
        }
        self.assertEqual(expected_flavors, ralph_flavors)

    def test_get_ralph_servers_data(self):
        ralph_projects = self.ralph_client.get_ralph_projects()
        ralph_projects_with_servers = self.ralph_client.get_ralph_servers_data(
            ralph_projects
        )
        self.assertIn(
            self.host.host_id,
            ralph_projects_with_servers[self.cloud_project_1.project_id][
                "servers"
            ].keys(),
        )
