# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import datetime

import reversion as revisions
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from ralph.data_center.models.physical import DataCenterAsset
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider
)

logger = logging.getLogger(__name__)

try:
    from keystoneclient.v2_0 import client as ks
    keystone_client_exists = True
except ImportError:
    keystone_client_exists = False

try:
    from novaclient import client as novac
    nova_client_exists = True
except ImportError:
    nova_client_exists = False


class EmptyList(Exception):
    def __init___(self, value):
        self.value = value

    def __str__(self):
        repr(self.value)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
        self.summary = defaultdict(int)
        self.openstack_projects = {}
        self.openstack_flavors = {}

    @staticmethod
    def _get_novaclient_connection(site):
        nt = novac.Client(
            site['version'],
            site['username'],
            site['password'],
            site['tenant_name'],
            site['auth_url']
        )
        return nt

    @staticmethod
    def _get_servers_list(nt, site):
        """
        Returns list of servers for a project.
        :parm site: novaclient connection
        """
        servers = []
        marker = None

        while True:
            try:
                servers_part = nt.servers.list(
                    search_opts={'all_tenants': True},
                    limit=1000,
                    marker=marker,
                )
                marker = servers_part[-1].id
                servers.extend(servers_part)
            except IndexError:
                break

        servers = list(map(lambda server: server.__dict__, servers))
        if len(servers) == 0:
            raise EmptyList('Got an empty list of instances from '
                            '{}'.format(site['auth_url']))
        return servers

    @staticmethod
    def _get_flavors_list(nt, site):
        """
        Return list of flavours
        :parm nt: novaclient connection
        :return: dict
        """
        flavors = list(map(lambda flavor: flavor.__dict__, nt.flavors.list()))

        if len(flavors) == 0:
            raise EmptyList('Got an empty list of flavors from '
                            '{}'.format(site['auth_url']))
        return flavors

    @staticmethod
    def _get_projects_map(site):
        """
        Returns a map tenant_id->tenant_name
        :rtype: dict
        """
        keystone_client = ks.Client(
            username=site['username'],
            password=site['password'],
            tenant_name=site['tenant_name'],
            auth_url=site['auth_url'],
        )

        projects = {}
        for project in keystone_client.tenants.list():
            projects[project.id] = {
                'name': project.name,
                'tag':  site['tag'],
                'servers': {},
            }

        if len(projects) == 0:
            raise EmptyList('Got an empty list of projects from '
                            '{}'.format(site['auth_url']))
        return projects

    def _process_openstack_instances(self):
        for site in settings.OPENSTACK_INSTANCES:
            nt = self._get_novaclient_connection(site)
            self.openstack_projects.update(self._get_projects_map(site))

            for server in self._get_servers_list(nt, site):
                project_id = server['_info']['tenant_id']
                host_id = server['_info']['hostId']
                new_server = {
                    'hostname': server['_info']['name'],
                    'flavor_id': server['_info']['flavor']['id'],
                    'tag': site['tag'],
                    'ips': [],
                    'created': server['_info']['created'],
                    'hypervisor': server['_info'][
                        'OS-EXT-SRV-ATTR:hypervisor_hostname'],
                }
                for zone in server['_info']['addresses']:
                    for ip in server['_info']['addresses'][zone]:
                        new_server['ips'].append(ip['addr'])
                try:
                    self.openstack_projects[project_id]['servers'][
                        host_id] = new_server
                except KeyError:
                    logger.warning('Project {} not found'.format(project_id))

            for flavor in self._get_flavors_list(nt, site):
                flavor_id = flavor['_info']['id']
                new_flavor = {
                    'name': flavor['_info']['name'],
                    'cores': flavor['_info']['vcpus'],
                    'memory': flavor['_info']['ram'],
                    'disk': flavor['_info']['disk']*1024,
                    'tag': site['tag'],
                }
                self.openstack_flavors[flavor_id] = new_flavor

    def _get_cloud_provider(self):
        """Get or create cloud provider object"""
        try:
            self.cloud_provider = CloudProvider.objects.get(name='openstack')
        except ObjectDoesNotExist:
            self.cloud_provider = CloudProvider(name='openstack')
            self._save_object(self.cloud_provider,
                              'Add openstack CloudProvider')

    def _get_ralph_data(self):
        """Get configuration from ralph DB"""
        self.ralph_projects = {}
        self.ralph_flavors = {}
        for project in CloudProject.objects.filter(
            cloudprovider=self.cloud_provider
        ):
            project_id = project.project_id
            self.ralph_projects[project_id] = {
                'name': project.name,
                'servers': {},
                'tags': project.tags.names(),
                'cloudprovider': project.cloudprovider,
            }

            for server in project.children.all():
                new_server = {'hostname': server.hostname,
                              'hypervisor': server.hypervisor,
                              'tags': server.tags.names(),
                              'ips': server.ip_addresses,
                              }
                host_id = server.host_id
                self.ralph_projects[project_id]['servers'][
                    host_id] = new_server

        for flavor in CloudFlavor.objects.filter(
            cloudprovider=self.cloud_provider
        ):
            self.ralph_flavors[flavor.flavor_id] = {'name': flavor.name}

    @staticmethod
    def _get_hypervisor(host_name):
        """get or None for CloudHost hypervisor"""
        try:
            obj = DataCenterAsset.objects.get(hostname=host_name)
            return obj
        except ObjectDoesNotExist:
            logger.error('Hypervisor {} not found in DataCenterAssets'.format(
                host_name
            ))
            return None

    def _add_server(self, openstack_server, server_id, project):
        """add new server to ralph"""
        try:
            flavor = CloudFlavor.objects.get(
                flavor_id=openstack_server['flavor_id']
            )
        except CloudFlavor.DoesNotExist:
            logger.warning(
                'Flavor not found for host {}'.format(openstack_server)
            )
            return
        new_server = CloudHost(
            hostname=openstack_server['hostname'],
            cloudflavor=flavor,
            parent=project,
            host_id=server_id,
            hypervisor=self._get_hypervisor(
                openstack_server['hypervisor']
            ),
            cloudprovider=self.cloud_provider,
        )

        # workaround - created field has auto_now_add attribute
        new_server.save()
        new_server.created = datetime.strptime(openstack_server['created'],
                                               self.DATETIME_FORMAT)
        self._save_object(new_server, 'add server %s'
                          % new_server.hostname)

        new_server.tags.add(openstack_server['tag'])
        with transaction.atomic(), revisions.create_revision():
            new_server.ip_addresses = openstack_server['ips']
            revisions.set_comment('Assign ip addresses to a host')

    def _update_server(self, openstack_server, server_id, ralph_server):
        """Compare and apply changes to a CloudHost"""
        modified = False
        obj = CloudHost.objects.get(host_id=server_id)
        flavor = CloudFlavor.objects.get(
            flavor_id=openstack_server['flavor_id']
        )

        if obj.hostname != openstack_server['hostname']:
            obj.hostname = openstack_server['hostname']
            self._save_object(obj, 'Modify hostname')
            modified = True

        if obj.cloudflavor != flavor:
            obj.cloudflavor = flavor
            self._save_object(obj, 'Modify cloudflavor')
            modified = True

        hypervisor = self._get_hypervisor(openstack_server['hypervisor'])
        if obj.hypervisor != hypervisor:
            obj.hypervisor = hypervisor
            self._save_object(obj, 'Modify hypervisor')
            modified = True

        if openstack_server['tag'] not in ralph_server['tags']:
            obj.tags.add(openstack_server['tag'])

        # add/remove IPs
        if set(openstack_server['ips']) != set(ralph_server['ips']):
            modified = True
            with transaction.atomic(), revisions.create_revision():
                obj.ip_addresses = openstack_server['ips']
                revisions.set_comment('Assign ip addresses to a host')

        return modified

    def _process_servers(self, servers, project):
        """Add/modify/remove servers within project"""
        for server_id, server in servers.items():
            try:
                modified = self._update_server(
                    server,
                    server_id,
                    self.ralph_projects[project.project_id]['servers'][
                        server_id],
                )

                if modified:
                    self.summary['mod_instances'] += 1

            except KeyError:
                self._add_server(server, server_id, project)
                self.summary['new_instances'] += 1

        self._cleanup_servers(servers, project.project_id)

    def _cleanup_servers(self, servers, project_id):
        """Remove servers which no longer exists in openstack project"""
        try:
            for server_id in (
                self.ralph_projects[project_id]['servers'].keys(
                ) - servers.keys()
            ):
                self._delete_object(CloudHost.objects.get(host_id=server_id))
                self.summary['del_instances'] += 1
        except KeyError:
            pass

    def _add_project(self, data, project_id):
        """Add/modify project in ralph"""
        if project_id in self.ralph_projects.keys():
            project = CloudProject.objects.get(project_id=project_id)
            if (
                self.ralph_projects[project_id]['name'] != data['name'] or
                self.openstack_projects[project_id]['tag']
                    not in self.ralph_projects[project_id]['tags']
            ):
                self.summary['mod_projects'] += 1
                project.cloudprovider = self.cloud_provider
                project.name = data['name']
                self._save_object(project, 'Modify name')
                project.tags.add(data['tag'])

        else:
            self.summary['new_projects'] += 1
            project = CloudProject(
                name=data['name'],
                project_id=project_id,
                cloudprovider=self.cloud_provider,
            )
            self._save_object(project, 'Add project %s' % project.name)
            project.tags.add(data['tag'])
        self._process_servers(data['servers'], project)

    def _add_flavor(self, flavor, flavor_id):
        """Add/modify flavor in ralph"""
        if flavor_id not in self.ralph_flavors:
            new_flavor = CloudFlavor(
                name=flavor['name'],
                flavor_id=flavor_id,
                cloudprovider=self.cloud_provider
            )
            self._save_object(new_flavor, 'Add new flavor')
            new_flavor.tags.add(flavor['tag'])
            for component in ['cores', 'memory', 'disk']:
                setattr(new_flavor, component, flavor[component])

            self.summary['new_flavors'] += 1
        else:
            mod = False
            obj = CloudFlavor.objects.get(flavor_id=flavor_id)
            if self.ralph_flavors[flavor_id]['name'] != flavor['name']:
                obj.name = flavor['name']
                self._save_object(obj, 'Change name')
                mod = True
            if flavor['tag'] not in obj.tags.names():
                obj.tags.add(flavor['tag'])
                mod = True

            for component in ['cores', 'memory', 'disk']:
                if flavor[component] != getattr(obj, component):
                    with transaction.atomic(), revisions.create_revision():
                        revisions.set_comment(
                            'Change {} value'.format(component)
                        )
                        setattr(obj, component, flavor[component])
                        mod = True

            if mod:
                self.summary['mod_flavors'] += 1

    def _update_ralph(self):
        """Update existing and add new ralph data"""

        for flavor_id in self.openstack_flavors:
            self._add_flavor(self.openstack_flavors[flavor_id], flavor_id)

        for project_id in self.openstack_projects:
            self._add_project(self.openstack_projects[project_id], project_id)

    def _cleanup(self):
        """
        Remove all projects and flavors that doesn't exist in openstack from
        ralph
        """
        for project_id in (set(self.ralph_projects.keys()) - set(
            self.openstack_projects.keys())
        ):
            self._delete_object(CloudProject.objects.get(
                project_id=project_id))

        for del_flavor in (
                set(self.ralph_flavors) - set(self.openstack_flavors)):
            self._delete_object(CloudFlavor.objects.get(flavor_id=del_flavor))
            self.summary['del_flavors'] += 1

    @staticmethod
    def _save_object(obj, comment):
        """Save an object and create revision"""
        with transaction.atomic(), revisions.create_revision():
            obj.save()
            revisions.set_comment(comment)

    @staticmethod
    def _delete_object(obj):
        """Save an object and delete revision"""
        with transaction.atomic(), revisions.create_revision():
            obj.delete()
            revisions.set_comment('openstack_sync::_delete_object')

    def _print_summary(self):
        """Print sync summary"""
        self.stdout.write("Openstack projects synced")
        self.stdout.write("New projects: {}".format(
            self.summary['new_projects']))
        self.stdout.write("Modified projects: {}".format(
            self.summary['mod_projects']))
        self.stdout.write("New instances: {}".format(
            self.summary['new_instances']))
        self.stdout.write("Modified instances: {}".format(
            self.summary['mod_instances']))
        self.stdout.write(
            "Deleted projects: {}".format(self.summary['del_projects']))
        self.stdout.write(
            "Deleted instances: {}".format(self.summary['del_instances']))
        self.stdout.write("Openstack flavors synced")
        self.stdout.write("New flavors: {}".format(
            self.summary['new_flavors']))
        self.stdout.write("Modified flavors: {}".format(
            self.summary['mod_flavors']))
        self.stdout.write("Deleted flavors: {}".format(
            self.summary['del_flavors']))

    def handle(self, *args, **options):
        if not nova_client_exists:
            logger.error("novaclient module is not installed")
            raise ImportError("No module named novaclient")
        if not keystone_client_exists:
            logger.error("keystoneclient module is not installed")
            raise ImportError("No module named keystoneclient")
        if not hasattr(settings, 'OPENSTACK_INSTANCES'):
            logger.error('Nothing to sync')
            return
        self.stdout.write("syncing...")
        self._get_cloud_provider()
        self._process_openstack_instances()
        self._get_ralph_data()
        self._update_ralph()
        self._cleanup()
        self._print_summary()
