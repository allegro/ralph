import logging
import re
from functools import lru_cache

from django.conf import settings

from ralph.lib import network
from ralph.settings import DEFAULT_OPENSTACK_PROVIDER_NAME

try:
    from keystoneauth1 import session as ks_session
    from keystoneauth1.identity import v3 as ks_v3_identity
    from keystoneclient.v2_0 import client as ks_v2_client
    from keystoneclient.v3 import client as ks_v3_client
    keystone_client_exists = True
except ImportError:
    keystone_client_exists = False

try:
    from novaclient import client as novac
    from novaclient.exceptions import NotFound
    nova_client_exists = True
except ImportError:
    nova_client_exists = False


try:
    from ironicclient.client import get_client as get_ironic_client
    ironic_client_exists = True
except ImportError:
    ironic_client_exists = False


logger = logging.getLogger(__name__)


class EmptyListError(Exception):
    def __init___(self, value):
        self.value = value

    def __str__(self):
        repr(self.value)


class RalphIronicClient:

    def __init__(self, os_conf):
        if not ironic_client_exists:
            logger.error("ironicclient module is not installed")
            raise ImportError("No module named ironicclient")
        self.ironic_client = get_ironic_client(
            api_version=os_conf.get('ironic-api-version', '1'),
            os_username=os_conf['username'],
            os_password=os_conf['password'],
            os_tenant_name=os_conf['tenant_name'],
            os_auth_url=os_conf['auth_url']
        )

    def get_nodes_list(self, associated=True, fields=None):
        if not fields:
            fields = ['extra', 'instance_uuid']
        return self.ironic_client.node.list(
            associated=associated,
            fields=fields
        )


class RalphOpenstackClient:
    """
    This is a single OpenStack instance client. It handles keystone
    authentication. It has methods to fetch OpenStack data useful from
    Ralph's perspective from openstack compute and openstack keystone.
    """
    def __init__(self, site):
        if not nova_client_exists:
            logger.error("novaclient module is not installed")
            raise ImportError("No module named novaclient")
        if not keystone_client_exists:
            logger.error("keystoneclient module is not installed")
            raise ImportError("No module named keystoneclient")

        self.session = self._get_keystone_session(site)
        self.nova_client = self._get_nova_client_connection(site)
        self.keystone_client = self._get_keystone_client(site)
        self.site = site

    def _get_nova_client_connection(self, site):
        if (
            site.get('keystone_auth_url') and
            site.get('keystone_version', '').startswith('3')
        ):
            nt = novac.Client(site['version'], session=self.session)
        else:
            nt = novac.Client(
                site['version'],
                site['username'],
                site['password'],
                site['tenant_name'],
                site['auth_url']
            )
        return nt

    def _get_keystone_client(self, site):
        if site.get('keystone_version', '').startswith('3'):
            client = ks_v3_client.Client(session=self.session, version=(3,))
        else:
            client = ks_v2_client.Client(
                username=site['username'],
                password=site['password'],
                tenant_name=site['tenant_name'],
                auth_url=site['auth_url'],
            )
        return client

    @staticmethod
    def _get_keystone_session(site):
        auth = ks_v3_identity.Password(
            auth_url=site.get('keystone_auth_url', site['auth_url']),
            username=site['username'],
            password=site['password'],
            user_domain_name=site.get('user_domain_name', 'default'),
            project_name=site['tenant_name'],
            project_domain_name=site.get('project_domain_name', 'default'),
        )
        return ks_session.Session(auth=auth)

    @lru_cache()
    def _get_images(self):
        logger.info('Fetching images')
        return {img.id: img.__dict__ for img in self.nova_client.images.list()}

    def get_image_name(self, image_id):
        try:
            return self._get_images()[image_id]['name']
        except KeyError:
            try:
                return self.nova_client.images.get(image_id).name
            except NotFound:
                return ''

    def get_flavors_list(self):
        """
        Return list of flavours
        """
        logger.info('Fetching flavors list from {}'.format(self.site['tag']))
        flavors = []
        for is_public in (True, False):
            flavors.extend(list(map(
                lambda fl: fl.__dict__, self.nova_client.flavors.list(
                    is_public=is_public
                )
            )))
        if len(flavors) == 0:
            raise EmptyListError(
                'Got an empty list of flavors from {}'.format(
                    self.site['auth_url']
                )
            )
        return flavors

    def get_servers_list(self, search_opts=None):
        """
        Returns list of servers for a project.
        """
        if not search_opts:
            search_opts = {}
        servers = []
        marker = None
        limit = 1000
        logger.info('Fetching servers list from {}'.format(self.site['tag']))
        while True:
            try:
                logger.debug(
                    'Fetching servers with marker {}'.format(marker)
                )
                servers_part = self.nova_client.servers.list(
                    search_opts=search_opts,
                    limit=limit,
                    marker=marker,
                )
                marker = servers_part[-1].id
                servers.extend(servers_part)
                if len(servers_part) < limit:
                    break
            except IndexError:
                break

        servers = list(map(lambda server: server.__dict__, servers))
        # If only an incremental update is being performed, it is possible
        # that no servers are returned. Otherwise, zero servers is an error.
        if len(servers) == 0 and not search_opts.get('changes-since'):
            raise EmptyListError(
                'Got an empty list of instances from {}'.format(
                    self.site['auth_url']
                )
            )
        logger.info('Fetched {} servers from {}'.format(
            len(servers), self.site['tag']
        ))
        return servers

    def get_keystone_projects(self):
        if self.keystone_client.version == 'v3':
            projects_resource = self.keystone_client.projects
        else:
            projects_resource = self.keystone_client.tenants
        yield from projects_resource.list()


class RalphOpenStackInfrastructureClient:
    """
    This is an OpenStack client designed to connect with multiple (or all)
    OpenStack instances that may exist in your local infrastructure.
    It instantiates a separate RalphOpenStackClient instance to communicate
    with each OpenStack instance. It has methods to extract
    and accumulate data from all instances in one place.
    """
    def __init__(self, openstack_provider_name):
        super().__init__()
        self.DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
        self.openstack_provider_name = openstack_provider_name
        self.clients = self._get_instances_from_settings()

    def _get_instances_from_settings(self):
        """
        Filter instances from OPENSTACK_INSTANCES (from settings) and
        initialize clients only for the ones matching current
        openstack provider.
        """
        clients = []
        for os_instance in settings.OPENSTACK_INSTANCES:
            if os_instance.get(
                'provider', DEFAULT_OPENSTACK_PROVIDER_NAME
            ) == self.openstack_provider_name:
                clients.append(RalphOpenstackClient(os_instance))
        return clients

    @classmethod
    def _get_flavor_data(cls, client, flavor):
        return {
            'name': flavor['name'],
            'cores': flavor['vcpus'],
            'memory': flavor['ram'],
            'disk': flavor['disk'] * 1024,
            'tag': client.site['tag'],
        }

    def get_openstack_flavors(self):
        openstack_flavors = {}
        for client in self.clients:
            logger.info('Processing {} ({})'.format(
                client.site['auth_url'], client.site['tag']
            ))
            for flavor in client.get_flavors_list():
                openstack_flavors[flavor['id']] = self._get_flavor_data(
                    client, flavor
                )
        return openstack_flavors

    def get_openstack_projects(self):
        openstack_projects = {}
        for client in self.clients:
            logger.info('Processing {} ({})'.format(
                client.site['auth_url'], client.site['tag']
            ))
            for project in client.get_keystone_projects():
                if project.id not in openstack_projects:
                    openstack_projects[project.id] = {
                        'name': project.name,
                        'servers': {},
                        'tags': []
                    }
                openstack_projects[project.id]['tags'].append(
                    client.site['tag']
                )
        return openstack_projects

    def get_openstack_instances_data(
        self, openstack_projects, openstack_flavors, search_opts=None
    ):
        """
        Take openstack_projects dictionary and populate it with instances
        (servers). If any flavor is missing, add it to the openstack_flavors
        dictionary.

        :param openstack_flavors: dictionary of openstack flavors
        :param openstack_projects: dictionary of openstack projects
        :return: updated openstack_projects and openstack_flavors
        :param search_opts: dictionary of search options
        """
        default_search_opts = {'all_tenants': True}
        if not search_opts:
            search_opts = {}
        search_opts.update(default_search_opts)

        for client in self.clients:
            logger.info('Processing {} ({})'.format(
                client.site['auth_url'], client.site['tag']
            ))
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
                    'hypervisor': server['OS-EXT-SRV-ATTR:hypervisor_hostname'],  # noqa: E501
                    'image': image_name,
                    'status': server['status']
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
                    openstack_projects[project_id]['servers'][host_id] = (
                        new_server
                    )
                except KeyError:
                    logger.warning(
                        'Project %s not found for server %s',
                        project_id, host_id
                    )

                if flavor_id not in openstack_flavors:
                    logger.warning(
                        'Flavor %s (found in host %s) not in flavors list.'
                        ' Fetching it', flavor_id, host_id)
                    flavor = client.nova_client.flavors.get(flavor_id).__dict__
                    openstack_flavors[flavor['id']] = self._get_flavor_data(
                        client,
                        flavor,
                    )
        return openstack_projects, openstack_flavors
