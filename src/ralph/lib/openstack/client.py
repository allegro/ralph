import logging
from functools import lru_cache

try:
    from keystoneclient.v2_0 import client as ks_v2_client
    from keystoneclient.v3 import client as ks_v3_client
    from keystoneauth1 import session as ks_session
    from keystoneauth1.identity import v3 as ks_v3_identity
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
        if len(servers) == 0:
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
