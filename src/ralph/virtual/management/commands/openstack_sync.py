# -*- coding: utf-8 -*-
import logging
import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache

import reversion as revisions
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib import network
from ralph.lib.openstack.client import RalphIronicClient, RalphOpenstackClient
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider
)

logger = logging.getLogger(__name__)

DEFAULT_OPENSTACK_PROVIDER_NAME = settings.DEFAULT_OPENSTACK_PROVIDER_NAME


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
        self.summary = defaultdict(int)
        self.openstack_projects = {}
        self.openstack_flavors = {}
        self.openstack_provider_name = DEFAULT_OPENSTACK_PROVIDER_NAME

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--provider',
            help='OpenStack provider name',
            default=DEFAULT_OPENSTACK_PROVIDER_NAME,
        )
        parser.add_argument(
            '--match-ironic-physical-hosts',
            action='store_true',
            help='Match physical hosts and baremetal instances'
        )
        parser.add_argument(
            '--node-serial-number-parameter',
            type=str,
            default='serial_number',
            help="Extra parameter used to store node serial numbers in Ironic"
        )
        parser.add_argument(
            '--asset-serial-number-parameter',
            type=str,
            default='sn',
            help="Parameter used to store asset serial numbers in Ralph"
        )

    def _update_projects(self, client):
        """
        Returns a map tenant_id->tenant_name
        :rtype: dict
        """
        for project in client.get_keystone_projects():
            if project.id not in self.openstack_projects:
                self.openstack_projects[project.id] = {
                    'name': project.name,
                    'servers': {},
                    'tags': []
                }
            self.openstack_projects[project.id]['tags'].append(
                client.site['tag']
            )

    def _get_instances_from_settings(self):
        """
        Filter instances from OPENSTACK_INSTANCES (from settings) and yield
        only the ones matching current opeenstack provider.
        """
        for os_instance in settings.OPENSTACK_INSTANCES:
            if os_instance.get(
                'provider', DEFAULT_OPENSTACK_PROVIDER_NAME
            ) == self.openstack_provider_name:
                yield RalphOpenstackClient(os_instance)

    def _process_openstack_instances(self):
        for client in self._get_instances_from_settings():
            logger.info('Processing {} ({})'.format(
                client.site['auth_url'], client.site['tag']
            ))
            self._update_projects(client)

            def _add_flavor(flavor):
                flavor_id = flavor['id']
                new_flavor = {
                    'name': flavor['name'],
                    'cores': flavor['vcpus'],
                    'memory': flavor['ram'],
                    'disk': flavor['disk'] * 1024,
                    'tag': client.site['tag'],
                }
                self.openstack_flavors[flavor_id] = new_flavor

            for flavor in client.get_flavors_list():
                _add_flavor(flavor)

            search_opts = {'all_tenants': True}
            for server in client.get_servers_list(search_opts=search_opts):
                project_id = server['tenant_id']
                host_id = server['id']
                image_name = client.get_image_name(
                     server['image']['id']
                ) if server['image'] else None
                flavor_id = server['flavor']['id']
                new_server = {
                    'hostname': None,
                    'id': server['id'],
                    'flavor_id': flavor_id,
                    'tag': client.site['tag'],
                    'ips': {},
                    'created': server['created'],
                    'hypervisor': server['OS-EXT-SRV-ATTR:hypervisor_hostname'],
                    'image': image_name,
                }
                for zone in server['addresses']:
                    if (
                        'network_regex' in client.site and
                        not re.match(client.site['network_regex'], zone)
                    ):
                        continue
                    for ip in server['addresses'][zone]:
                        addr = ip['addr']
                        # fetch FQDN from DNS by IP address
                        hostname = network.hostname(addr)
                        logger.debug('Get IP {} ({}) for {}'.format(
                            addr, hostname, server['id']
                        ))
                        new_server['ips'][addr] = hostname
                        if not new_server['hostname']:
                            new_server['hostname'] = hostname
                # fallback to default behavior if FQDN could not be fetched
                # from DNS
                new_server['hostname'] = (
                    new_server['hostname'] or server['name']
                )
                try:
                    self.openstack_projects[project_id]['servers'][host_id] = (
                        new_server
                    )
                except KeyError:
                    logger.warning(
                        'Project %s not found for server %s',
                        project_id, host_id
                    )

                if flavor_id not in self.openstack_flavors:
                    logger.warning(
                        'Flavor %s (found in host %s) not in flavors list.'
                        ' Fetching it', flavor_id, host_id)
                    _add_flavor(client.nova_client.flavors.get(flavor_id).__dict__)

    def _get_cloud_provider(self):
        """Get or create cloud provider object"""
        def _get_or_create(provider_name):
            try:
                cloud_provider = CloudProvider.objects.get(
                    name=provider_name,
                )
            except ObjectDoesNotExist:
                cloud_provider = CloudProvider(
                    name=provider_name,
                )
                self._save_object(
                    cloud_provider, 'Add {} CloudProvider'.format(provider_name)
                )
            return cloud_provider
        self.cloud_provider = _get_or_create(self.openstack_provider_name)
        self.default_cloud_provider = _get_or_create(
            DEFAULT_OPENSTACK_PROVIDER_NAME
        )

    def _get_ralph_data(self):
        """Get configuration from ralph DB"""
        self.ralph_projects = {}
        self.ralph_flavors = {}
        projects = CloudProject.objects.filter(
            cloudprovider=self.cloud_provider
        ).prefetch_related('tags')

        def _get_project_info(project):
            return {
                'name': project.name,
                'servers': {},
                'tags': project.tags.names(),
            }

        for project in projects:
            project_id = project.project_id
            self.ralph_projects[project_id] = _get_project_info(project)

        for server in CloudHost.objects.filter(
            cloudprovider=self.cloud_provider,
        ).select_related(
            'hypervisor', 'parent', 'parent__cloudproject',
        ).prefetch_related('tags'):
            ips = dict(
                server.ethernet_set.select_related('ipaddress').values_list(
                    'ipaddress__address', 'ipaddress__hostname'
                )
            )
            new_server = {
                'hostname': server.hostname,
                'hypervisor': server.hypervisor,
                'tags': server.tags.names(),
                'ips': ips,
                'host_id': server.host_id,
            }
            host_id = server.host_id
            project_id = server.parent.cloudproject.project_id
            # workaround for projects with the same id in multiple providers
            if project_id not in self.ralph_projects:
                self.ralph_projects[project_id] = _get_project_info(
                    CloudProject.objects.get(project_id=project_id)
                )
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
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            logger.warning('Hypervisor %s not found for %s',
                           host_name, server_id)
            return None

    def _match_physical_and_cloud_hosts(self):
        """Connect CloudHosts and DC assets according to data from Ironic."""

        for os_conf in settings.OPENSTACK_INSTANCES:
            if (
                os_conf.get('provider', DEFAULT_OPENSTACK_PROVIDER_NAME) !=
                self.openstack_provider_name
            ):
                continue

            client = RalphIronicClient(os_conf=os_conf)
            self._match_nodes_to_hosts(client.get_nodes_list())

    def _match_nodes_to_hosts(self, nodes):
        """Match iornic nodes to hosts."""

        not_found_message_tpl = (
            '%s with the host id or serial number %s was not found. Check if '
            'Ralph is synchronized with OpenStack or add it manually.'
        )

        for node in nodes:
            node_sn = node.extra[self.ironic_serial_number_param]

            try:
                host = CloudHost.objects.get(host_id=node.instance_uuid)
                asset = DataCenterAsset.objects.get(
                    **{self.ralph_serial_number_param: node_sn}
                )
            except DataCenterAsset.DoesNotExist:
                logger.warning(
                    not_found_message_tpl,
                    'DC asset',
                    node_sn
                )
            except CloudHost.DoesNotExist:
                logger.warning(
                    not_found_message_tpl,
                    'Cloud host',
                    node.instance_uuid
                )
            except DataCenterAsset.MultipleObjectsReturned:
                logger.error(
                    'Multiple DC assets were found for the serial number %s. '
                    'Please match Cloud host %s manually.',
                    node_sn,
                    host.id
                )
            except KeyError:
                logger.warning(
                    'Could not get serial number of the Ironic node %s using '
                    '%s extra parameter. Please check the configuration '
                    'of the node and submit a proper extra parameter or match '
                    'the node manually.',
                    node.uuid, self.ironic_serial_number_param
                )
            else:
                logger.info(
                    'Cloud host %s matched DC asset %s.',
                    host.id,
                    asset.id
                )
                if host.hypervisor != asset:
                    host.hypervisor = asset
                    host.save()

    @lru_cache()
    def _get_flavors(self):
        return {fl.flavor_id: fl for fl in CloudFlavor.objects.all()}

    def _add_server(self, openstack_server, server_id, project):
        """add new server to ralph"""
        try:
            flavor = self._get_flavors()[openstack_server['flavor_id']]
        except KeyError:
            logger.warning(
                'Flavor %s not found for host %s',
                openstack_server['flavor_id'], openstack_server
            )
            return
        logger.info(
            'Creating new server %s (%s)',
            server_id, openstack_server['hostname']
        )
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
        try:
            flavor = self._get_flavors()[openstack_server['flavor_id']]
        except KeyError:
            logger.warning(
                'Flavor %s not found for host %s',
                openstack_server['flavor_id'], openstack_server
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
        if openstack_server['ips'] != ralph_server['ips']:
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
                host = CloudHost.objects.get(host_id=server_id)
                logger.warning(
                    'Removing CloudHost %s (%s)',
                    server_id, host.hostname
                )
                self._delete_object(host)
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
            try:
                with transaction.atomic():
                    self._save_object(project, 'Add project %s' % project.name)
            except IntegrityError:
                logger.warning(
                    'Duplicated project ID (%s) for project %s',
                    project.project_id, project.name
                )
                project = CloudProject.objects.get(
                    project_id=project_id
                )
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
        Remove all projects and flavors that don't exist in openstack from
        ralph
        """
        for project_id in (set(self.ralph_projects.keys()) - set(
            self.openstack_projects.keys())
        ):
            cloud_project = CloudProject.objects.get(
                project_id=project_id,
                cloudprovider=self.cloud_provider
            )
            if not cloud_project:
                continue
            children_count = cloud_project.children.count()
            logger_extras = {
                'cloud_project_name': cloud_project.name,
                'cloud_project_id': cloud_project.id
            }
            if children_count == 0:
                self._delete_object(cloud_project)
                logger.debug(
                    'Deleted Cloud Project (name: {}, id: {})'.format(
                        cloud_project.name,
                        cloud_project.id,
                    ),
                    extra=logger_extras
                )
                self.summary['del_projects'] += 1
            else:
                logger.error(
                    'Cloud project name: %s id: %s cant\'t be deleted '
                    'because it has %s children',
                    cloud_project.name,
                    cloud_project.id,
                    children_count,
                    extra=logger_extras
                )

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
        logger.warning('Deleting %s (id: %s)', obj, obj.id)
        with transaction.atomic(), revisions.create_revision():
            obj.delete()
            revisions.set_comment('openstack_sync::_delete_object')

    def _print_summary(self):
        """
        Print sync summary
        Python 3.6 raises KeyError when using .format(**self.summary) for a
        nonexistent key. A nonexistent key has to be specified explicitly for
        defaultdict to work as expected.
        """
        msg = """Openstack projects synced

        New projects:       {summary[new_projects]}
        Modified projects:  {summary[mod_projects]}
        Deleted projects:   {summary[del_projects]}
        Total projects:     {summary[total_projects]}

        New instances:      {summary[new_instances]}
        Modified instances: {summary[mod_instances]}
        Deleted instances:  {summary[del_instances]}
        Total instances:    {summary[total_instances]}

        New flavors:        {summary[new_flavors]}
        Modified flavors:   {summary[mod_flavors]}
        Deleted flavors:    {summary[del_flavors]}
        Total flavors:      {summary[total_flavors]}""".format(
            summary=self.summary
        )

        self.stdout.write(msg)
        logger.info(msg)

    def handle(self, *args, **options):
        try:
            logger.info('Openstack sync started...')
            match_ironic = options.get('match_ironic_physical_hosts')
            if not hasattr(settings, 'OPENSTACK_INSTANCES'):
                logger.error('Nothing to sync')
                return
            self.openstack_provider_name = options['provider']
            self.ironic_serial_number_param = options[
                'node_serial_number_parameter'
            ]
            self.ralph_serial_number_param = options[
                'asset_serial_number_parameter'
            ]

            self._get_cloud_provider()
            self._process_openstack_instances()
            self._get_ralph_data()
            self._update_ralph()

            if match_ironic:
                self._match_physical_and_cloud_hosts()

            self._cleanup()
            self._print_summary()
        except Exception as err:
            logger.exception(
                'Openstack sync failed with error: {}'.format(err)
            )
