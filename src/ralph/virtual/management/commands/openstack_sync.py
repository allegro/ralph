# -*- coding: utf-8 -*-
import logging
import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache

import reversion as revisions
from dateutil import parser
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
    from novaclient.exceptions import NotFound
    nova_client_exists = True
except ImportError:
    nova_client_exists = False


class EmptyListError(Exception):
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
        logger.info('Fetching servers list from {}'.format(site['tag']))
        while True:
            try:
                logger.debug(
                    'Fetching servers with marker {}'.format(marker)
                )
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
            raise EmptyListError(
                'Got an empty list of instances from {}'.format(
                    site['auth_url']
                )
            )
        logger.info('Fetched {} servers from {}'.format(
            len(servers), site['tag']
        ))
        return servers

    @lru_cache()
    def _get_images(self, nt):
        logger.info('Fetching images')
        return {img.id: img.__dict__ for img in nt.images.list()}

    def _get_image_name(self, nt, image_id):
        try:
            return self._get_images(nt)[image_id]['name']
        except KeyError:
            try:
                return nt.images.get(image_id).name
            except NotFound:
                return ''

    @staticmethod
    def _get_flavors_list(nt, site):
        """
        Return list of flavours
        :parm nt: novaclient connection
        :return: dict
        """
        logger.info('Fetching flavors list from {}'.format(site['tag']))
        flavors = []
        for is_public in (True, False):
            flavors.extend(list(map(
                lambda fl: fl.__dict__, nt.flavors.list(is_public=is_public)
            )))
        if len(flavors) == 0:
            raise EmptyListError(
                'Got an empty list of flavors from {}'.format(site['auth_url'])
            )
        return flavors

    def _update_projects(self, site):
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

        for project in keystone_client.tenants.list():
            if project.id not in self.openstack_projects:
                self.openstack_projects[project.id] = {
                    'name': project.name,
                    'servers': {},
                    'tags': []
                }
            self.openstack_projects[project.id]['tags'].append(site['tag'])

    def _process_openstack_instances(self):
        for site in settings.OPENSTACK_INSTANCES:
            logger.info('Processing {} ({})'.format(
                site['auth_url'], site['tag']
            ))
            nt = self._get_novaclient_connection(site)
            self._update_projects(site)

            def _add_flavor(flavor):
                flavor_id = flavor['id']
                new_flavor = {
                    'name': flavor['name'],
                    'cores': flavor['vcpus'],
                    'memory': flavor['ram'],
                    'disk': flavor['disk'] * 1024,
                    'tag': site['tag'],
                }
                self.openstack_flavors[flavor_id] = new_flavor

            for flavor in self._get_flavors_list(nt, site):
                _add_flavor(flavor)

            for server in self._get_servers_list(nt, site):
                project_id = server['tenant_id']
                host_id = server['id']
                image_name = self._get_image_name(
                    nt, server['image']['id']
                ) if server['image'] else None
                flavor_id = server['flavor']['id']
                new_server = {
                    'hostname': server['name'],
                    'id': server['id'],
                    'flavor_id': flavor_id,
                    'tag': site['tag'],
                    'ips': [],
                    'created': server['created'],
                    'hypervisor': server['OS-EXT-SRV-ATTR:hypervisor_hostname'],
                    'image': image_name,
                }
                for zone in server['addresses']:
                    if (
                        'network_regex' in site and
                        not re.match(site['network_regex'], zone)
                    ):
                        continue
                    for ip in server['addresses'][zone]:
                        new_server['ips'].append(ip['addr'])
                try:
                    self.openstack_projects[project_id]['servers'][host_id] = (
                        new_server
                    )
                except KeyError:
                    logger.error('Project {} not found for server {}'.format(
                        project_id, host_id,
                    ))

                if flavor_id not in self.openstack_flavors:
                    logger.warning((
                        'Flavor {} (found in host {}) not in flavors list.'
                        ' Fetching it'
                    ).format(flavor_id, host_id))
                    _add_flavor(nt.flavors.get(flavor_id).__dict__)

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
        projects = CloudProject.objects.filter(
            cloudprovider=self.cloud_provider
        ).prefetch_related('tags')
        for project in projects:
            project_id = project.project_id
            self.ralph_projects[project_id] = {
                'name': project.name,
                'servers': {},
                'tags': project.tags.names(),
            }

        for server in CloudHost.objects.filter(
            parent__in=projects
        ).select_related(
            'hypervisor', 'parent', 'parent__cloudproject',
        ).prefetch_related(
            'ipaddress_set', 'tags'
        ):
            new_server = {
                'hostname': server.hostname,
                'hypervisor': server.hypervisor,
                'tags': server.tags.names(),
                'ips': [ip.address for ip in server.ipaddress_set.all()],
                'host_id': server.host_id,
            }
            host_id = server.host_id
            project_id = server.parent.cloudproject.project_id
            self.ralph_projects[project_id]['servers'][host_id] = new_server

        for flavor in CloudFlavor.objects.filter(
            cloudprovider=self.cloud_provider
        ):
            self.ralph_flavors[flavor.flavor_id] = {'name': flavor.name}

    @staticmethod
    def _get_hypervisor(host_name, server_id):
        """get or None for CloudHost hypervisor"""
        try:
            obj = DataCenterAsset.objects.get(hostname=host_name)
            return obj
        except ObjectDoesNotExist:
            logger.error('Hypervisor {} not found for {}'.format(
                host_name, server_id,
            ))
            return None

    @lru_cache()
    def _get_flavors(self):
        return {fl.flavor_id: fl for fl in CloudFlavor.objects.all()}

    def _add_server(self, openstack_server, server_id, project):
        """add new server to ralph"""
        try:
            flavor = self._get_flavors()[openstack_server['flavor_id']]
        except KeyError:
            logger.error(
                'Flavor {} not found for host {}'.format(
                    openstack_server['flavor_id'], openstack_server
                )
            )
            return
        logger.info('Creating new server {} ({})'.format(
            server_id, openstack_server['hostname']
        ))
        new_server = CloudHost(
            hostname=openstack_server['hostname'],
            cloudflavor=flavor,
            parent=project,
            host_id=server_id,
            hypervisor=self._get_hypervisor(
                openstack_server['hypervisor'], server_id
            ),
            cloudprovider=self.cloud_provider,
            image_name=openstack_server['image'],
        )

        # workaround - created field has auto_now_add attribute
        new_server.save()
        new_server.created = parser.parse(openstack_server['created'])
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
        try:
            flavor = self._get_flavors()[openstack_server['flavor_id']]
        except KeyError:
            logger.error(
                'Flavor {} not found for host {}'.format(
                    openstack_server['flavor_id'], openstack_server
                )
            )
            return

        if obj.hostname != openstack_server['hostname']:
            logger.info('Updating hostname ({}) for {}'.format(
                openstack_server['hostname'], server_id
            ))
            obj.hostname = openstack_server['hostname']
            self._save_object(obj, 'Modify hostname')
            modified = True

        if obj.cloudflavor != flavor:
            logger.info('Updating flavor ({}) for {}'.format(
                flavor, server_id
            ))
            obj.cloudflavor = flavor
            self._save_object(obj, 'Modify cloudflavor')
            modified = True

        hypervisor = self._get_hypervisor(
            openstack_server['hypervisor'], server_id
        )
        if obj.hypervisor != hypervisor:
            logger.info('Updating hypervisor ({}) for {}'.format(
                hypervisor, server_id
            ))
            obj.hypervisor = hypervisor
            self._save_object(obj, 'Modify hypervisor')
            modified = True

        if obj.image_name != openstack_server['image']:
            logger.info('Updating image ({}) for {}'.format(
                openstack_server['image'], server_id
            ))
            obj.image_name = openstack_server['image']
            self._save_object(obj, 'Updated image info')
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
                ralph_server = (
                    self.ralph_projects[project.project_id]['servers'][server_id]  # noqa
                )
            except KeyError:
                self._add_server(server, server_id, project)
                self.summary['new_instances'] += 1
            else:
                modified = self._update_server(
                    server,
                    server_id,
                    ralph_server,
                )
                if modified:
                    self.summary['mod_instances'] += 1
            self.summary['total_instances'] += 1
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
            ralph_project = self.ralph_projects[project_id]
            modified = False
            if ralph_project['name'] != data['name']:
                modified = True
                project.name = data['name']
                self._save_object(project, 'Modify name')
            if not all([tag in ralph_project['tags'] for tag in data['tags']]):
                modified = True
                for tag in data['tags']:
                    project.tags.add(tag)
            if modified:
                self.summary['mod_projects'] += 1
        else:
            self.summary['new_projects'] += 1
            project = CloudProject(
                name=data['name'],
                project_id=project_id,
                cloudprovider=self.cloud_provider,
            )
            self._save_object(project, 'Add project %s' % project.name)
            for tag in data['tags']:
                project.tags.add(tag)
        self.summary['total_projects'] += 1
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
        self.summary['total_flavors'] += 1

    def _update_ralph(self):
        """Update existing and add new ralph data"""
        logger.info('Updating Ralph entries')
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
        logger.info('Saving {} (id: {}; {})'.format(obj, obj.id, comment))
        with transaction.atomic(), revisions.create_revision():
            obj.save()
            revisions.set_comment(comment)

    @staticmethod
    def _delete_object(obj):
        """Save an object and delete revision"""
        logger.warning('Deleting {} (id: {})'.format(obj, obj.id))
        with transaction.atomic(), revisions.create_revision():
            obj.delete()
            revisions.set_comment('openstack_sync::_delete_object')

    def _print_summary(self):
        """Print sync summary"""
        msg = """Openstack projects synced

        New projects:       {new_projects}
        Modified projects:  {mod_projects}
        Deleted projects:   {del_projects}
        Total projects:     {total_projects}

        New instances:      {new_instances}
        Modified instances: {mod_instances}
        Deleted instances:  {del_instances}
        Total instances:    {total_instances}

        New flavors:        {new_flavors}
        Modified flavors:   {mod_flavors}
        Deleted flavors:    {del_flavors}
        Total flavors:      {total_flavors}""".format(**self.summary)

        self.stdout.write(msg)
        logger.info(msg)

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
