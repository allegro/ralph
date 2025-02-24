# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import auto, Enum
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from reversion import revisions

from ralph.data_center.models.physical import DataCenterAsset
from ralph.lib.openstack.client import (
    RalphIronicClient,
    RalphOpenStackInfrastructureClient
)
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider
)

logger = logging.getLogger(__name__)

DEFAULT_OPENSTACK_PROVIDER_NAME = settings.DEFAULT_OPENSTACK_PROVIDER_NAME


class SynchronizationType(Enum):
    INCREMENTAL = auto()
    FULL = auto()


class RalphClient:
    def __init__(
        self,
        openstack_provider_name,
        ironic_serial_number_param,
        ralph_serial_number_param,
        changes_since=None,
    ):
        self.cloud_provider = self._get_or_create_cloud_provider(
            openstack_provider_name
        )
        self.openstack_provider_name = openstack_provider_name
        self.ironic_serial_number_param = ironic_serial_number_param
        self.ralph_serial_number_param = ralph_serial_number_param
        self.DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        self.summary = defaultdict(int)
        if changes_since:
            self.summary["sync_type"] = SynchronizationType.INCREMENTAL.name
        else:
            self.summary["sync_type"] = SynchronizationType.FULL.name

    def _get_or_create_cloud_provider(self, provider_name):
        """Get or create cloud provider object"""
        try:
            cloud_provider = CloudProvider.objects.get(
                name=provider_name,
            )
        except ObjectDoesNotExist:
            cloud_provider = CloudProvider(
                name=provider_name,
            )
            self._save_object(
                cloud_provider, "Add {} CloudProvider".format(provider_name)
            )
        return cloud_provider

    @classmethod
    def _get_project_info(cls, project):
        return {
            "name": project.name,
            "servers": {},
            "tags": list(project.tags.names()),
        }

    def get_ralph_projects(self):
        ralph_projects = {}
        projects = CloudProject.objects.filter(
            cloudprovider=self.cloud_provider
        ).prefetch_related("tags")

        for project in projects:
            project_id = project.project_id
            ralph_projects[project_id] = self._get_project_info(project)
        return ralph_projects

    def get_ralph_flavors(self):
        ralph_flavors = {}
        for flavor in CloudFlavor.objects.filter(cloudprovider=self.cloud_provider):
            ralph_flavors[flavor.flavor_id] = {"name": flavor.name}
        return ralph_flavors

    def get_ralph_servers_data(self, ralph_projects):
        """Get configuration from ralph DB"""
        for server in (
            CloudHost.objects.filter(
                cloudprovider=self.cloud_provider,
            )
            .select_related(
                "hypervisor",
                "parent",
                "parent__cloudproject",
            )
            .prefetch_related("tags")
        ):
            ips = dict(
                server.ethernet_set.select_related("ipaddress").values_list(
                    "ipaddress__address", "ipaddress__hostname"
                )
            )
            new_server = {
                "hostname": server.hostname,
                "hypervisor": server.hypervisor,
                "tags": server.tags.names(),
                "ips": ips,
                "host_id": server.host_id,
            }
            host_id = server.host_id
            project_id = server.parent.cloudproject.project_id
            # workaround for projects with the same id in multiple providers
            if project_id not in ralph_projects:
                ralph_projects[project_id] = self._get_project_info(
                    CloudProject.objects.get(project_id=project_id)
                )
            ralph_projects[project_id]["servers"][host_id] = new_server
        return ralph_projects

    @staticmethod
    def _get_hypervisor(host_name, server_id):
        """get or None for CloudHost hypervisor"""
        try:
            obj = DataCenterAsset.objects.get(hostname=host_name)
            return obj
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            logger.warning("Hypervisor %s not found for %s", host_name, server_id)
            return None

    def match_physical_and_cloud_hosts(self):
        """Connect CloudHosts and DC assets according to data from Ironic."""

        for os_conf in settings.OPENSTACK_INSTANCES:
            if (
                os_conf.get("provider", DEFAULT_OPENSTACK_PROVIDER_NAME)
                != self.openstack_provider_name
            ):
                continue

            client = RalphIronicClient(os_conf=os_conf)
            self._match_nodes_to_hosts(client.get_nodes_list())

    def _match_nodes_to_hosts(self, nodes):
        """Match iornic nodes to hosts."""

        not_found_message_tpl = (
            "%s with the host id or serial number %s was not found. Check if "
            "Ralph is synchronized with OpenStack or add it manually."
        )

        for node in nodes:
            node_sn = node.extra[self.ironic_serial_number_param]

            try:
                host = CloudHost.objects.get(host_id=node.instance_uuid)
                asset = DataCenterAsset.objects.get(
                    **{self.ralph_serial_number_param: node_sn}
                )
            except DataCenterAsset.DoesNotExist:
                logger.warning(not_found_message_tpl, "DC asset", node_sn)
            except CloudHost.DoesNotExist:
                logger.warning(not_found_message_tpl, "Cloud host", node.instance_uuid)
            except DataCenterAsset.MultipleObjectsReturned:
                logger.error(
                    "Multiple DC assets were found for the serial number %s. "
                    "Please match Cloud host %s manually.",
                    node_sn,
                    host.id,
                )
            except KeyError:
                logger.warning(
                    "Could not get serial number of the Ironic node %s using "
                    "%s extra parameter. Please check the configuration "
                    "of the node and submit a proper extra parameter or match "
                    "the node manually.",
                    node.uuid,
                    self.ironic_serial_number_param,
                )
            else:
                logger.info("Cloud host %s matched DC asset %s.", host.id, asset.id)
                if host.hypervisor != asset:
                    host.hypervisor = asset
                    host.save()

    @lru_cache()
    def _get_flavor_objects(self):
        return {fl.flavor_id: fl for fl in CloudFlavor.objects.all()}

    def _add_server(self, openstack_server, server_id, project_id):
        """add new server to ralph"""
        try:
            project = CloudProject.objects.get(project_id=project_id)
        except (CloudProject.DoesNotExist, CloudProject.MultipleObjectsReturned) as err:
            logger.warning(
                "Unable to assign project id of %s for host %s. Reason: %s",
                project_id,
                openstack_server,
                err,
            )
            return
        try:
            flavor = self._get_flavor_objects()[openstack_server["flavor_id"]]
        except KeyError:
            logger.warning(
                "Flavor %s not found for host %s",
                openstack_server["flavor_id"],
                openstack_server,
            )
            return
        logger.info(
            "Creating new server %s (%s)", server_id, openstack_server["hostname"]
        )
        new_server = CloudHost(
            hostname=openstack_server["hostname"],
            cloudflavor=flavor,
            parent=project,
            host_id=server_id,
            hypervisor=self._get_hypervisor(openstack_server["hypervisor"], server_id),
            cloudprovider=self.cloud_provider,
            image_name=openstack_server["image"],
        )

        # workaround - created field has auto_now_add attribute
        new_server.save()
        new_server.created = datetime.strptime(
            openstack_server["created"], self.DATETIME_FORMAT
        )
        self._save_object(new_server, "add server %s" % new_server.hostname)

        new_server.tags.add(openstack_server["tag"])
        with transaction.atomic(), revisions.create_revision():
            new_server.ip_addresses = openstack_server["ips"]
            revisions.set_comment("Assign ip addresses to a host")

    def _update_server(self, openstack_server, server_id, ralph_server):
        """Compare and apply changes to a CloudHost"""
        modified = False
        obj = CloudHost.objects.get(host_id=server_id)
        try:
            flavor = self._get_flavor_objects()[openstack_server["flavor_id"]]
        except KeyError:
            logger.warning(
                "Flavor %s not found for host %s",
                openstack_server["flavor_id"],
                openstack_server,
            )
            return

        if obj.hostname != openstack_server["hostname"]:
            logger.info(
                "Updating hostname ({}) for {}".format(
                    openstack_server["hostname"], server_id
                )
            )
            obj.hostname = openstack_server["hostname"]
            self._save_object(obj, "Modify hostname")
            modified = True

        if obj.cloudflavor != flavor:
            logger.info("Updating flavor ({}) for {}".format(flavor, server_id))
            obj.cloudflavor = flavor
            self._save_object(obj, "Modify cloudflavor")
            modified = True

        hypervisor = self._get_hypervisor(openstack_server["hypervisor"], server_id)
        if obj.hypervisor != hypervisor:
            logger.info("Updating hypervisor ({}) for {}".format(hypervisor, server_id))
            obj.hypervisor = hypervisor
            self._save_object(obj, "Modify hypervisor")
            modified = True

        if obj.image_name != openstack_server["image"]:
            logger.info(
                "Updating image ({}) for {}".format(
                    openstack_server["image"], server_id
                )
            )
            obj.image_name = openstack_server["image"]
            self._save_object(obj, "Updated image info")
            modified = True

        if openstack_server["tag"] not in ralph_server["tags"]:
            obj.tags.add(openstack_server["tag"])

        # add/remove IPs
        if openstack_server["ips"] != ralph_server["ips"]:
            modified = True
            with transaction.atomic(), revisions.create_revision():
                obj.ip_addresses = openstack_server["ips"]
                revisions.set_comment("Assign ip addresses to a host")

        return modified

    def _add_or_update_servers(
        self, openstack_project_servers, openstack_project_id, ralph_projects
    ):
        """Add/modify servers within project"""
        for server_id, server in openstack_project_servers.items():
            # In case of incremental sync, servers with DELETED status are
            # included in data received from Openstack. This method only
            # updates servers or creates new ones. There is a separate method
            # for server deletion (`_delete_servers`).
            if server["status"] == "DELETED":
                continue
            try:
                ralph_server = (
                    ralph_projects[openstack_project_id]["servers"][server_id]  # noqa
                )
            except KeyError:
                self._add_server(server, server_id, openstack_project_id)
                self.summary["new_instances"] += 1
            else:
                modified = self._update_server(
                    server,
                    server_id,
                    ralph_server,
                )
                if modified:
                    self.summary["mod_instances"] += 1
            self.summary["total_instances"] += 1

    def _calculate_servers_to_delete(
        self, openstack_project_servers, openstack_project_id, ralph_projects
    ):
        project = ralph_projects.get(openstack_project_id, None)
        if project:
            return list(project["servers"].keys() - openstack_project_servers.keys())
        return []

    def _calculate_servers_to_delete_incremental(self, openstack_project_servers):
        return [
            server
            for server, data in openstack_project_servers.items()
            if data.get("status") == "DELETED"
        ]

    def _delete_servers(self, servers):
        """Remove servers which no longer exists in openstack project"""
        try:
            for server_id in servers:
                host = CloudHost.objects.get(host_id=server_id)
                logger.warning("Removing CloudHost %s (%s)", server_id, host.hostname)
                self._delete_object(host)
                self.summary["del_instances"] += 1
        except (KeyError, ObjectDoesNotExist):
            pass

    def _add_or_update_projects(
        self, openstack_project_data, openstack_project_id, ralph_projects
    ):
        """Add/modify project in ralph"""
        if openstack_project_id in ralph_projects.keys():
            project = CloudProject.objects.get(project_id=openstack_project_id)
            ralph_project = ralph_projects[openstack_project_id]
            modified = False
            if ralph_project["name"] != openstack_project_data["name"]:
                modified = True
                project.name = openstack_project_data["name"]
                self._save_object(project, "Modify name")
            if not all(
                [tag in ralph_project["tags"] for tag in openstack_project_data["tags"]]
            ):
                modified = True
                for tag in openstack_project_data["tags"]:
                    project.tags.add(tag)
            if modified:
                self.summary["mod_projects"] += 1
        else:
            self.summary["new_projects"] += 1
            project = CloudProject(
                name=openstack_project_data["name"],
                project_id=openstack_project_id,
                cloudprovider=self.cloud_provider,
            )
            try:
                with transaction.atomic():
                    self._save_object(project, "Add project %s" % project.name)
            except IntegrityError:
                logger.warning(
                    "Duplicated project ID (%s) for project %s",
                    project.project_id,
                    project.name,
                )
                project = CloudProject.objects.get(project_id=openstack_project_id)
            for tag in openstack_project_data["tags"]:
                project.tags.add(tag)
        self.summary["total_projects"] += 1

    def _add_or_modify_flavours(self, flavor, flavor_id, ralph_flavors):
        """Add/modify flavor in ralph"""
        if flavor_id not in ralph_flavors:
            new_flavor = CloudFlavor(
                name=flavor["name"],
                flavor_id=flavor_id,
                cloudprovider=self.cloud_provider,
            )
            self._save_object(new_flavor, "Add new flavor")
            new_flavor.tags.add(flavor["tag"])
            for component in ["cores", "memory", "disk"]:
                setattr(new_flavor, component, flavor[component])

            self.summary["new_flavors"] += 1
        else:
            mod = False
            obj = CloudFlavor.objects.get(flavor_id=flavor_id)
            if ralph_flavors[flavor_id]["name"] != flavor["name"]:
                obj.name = flavor["name"]
                self._save_object(obj, "Change name")
                mod = True
            if flavor["tag"] not in obj.tags.names():
                obj.tags.add(flavor["tag"])
                mod = True

            for component in ["cores", "memory", "disk"]:
                if flavor[component] != getattr(obj, component):
                    with transaction.atomic(), revisions.create_revision():
                        revisions.set_comment("Change {} value".format(component))
                        setattr(obj, component, flavor[component])
                        mod = True

            if mod:
                self.summary["mod_flavors"] += 1
        self.summary["total_flavors"] += 1

    def perform_update(
        self, openstack_projects, openstack_flavors, ralph_projects, ralph_flavors
    ):
        """Update existing and add new ralph data"""
        logger.info("Updating Ralph entries")
        for flavor_id in openstack_flavors:
            self._add_or_modify_flavours(
                openstack_flavors[flavor_id], flavor_id, ralph_flavors
            )

        for project_id in openstack_projects:
            self._add_or_update_projects(
                openstack_projects[project_id], project_id, ralph_projects
            )
            self._add_or_update_servers(
                openstack_projects[project_id]["servers"], project_id, ralph_projects
            )

    def calculate_servers_to_delete(
        self, openstack_projects, ralph_projects, incremental=False
    ):
        servers_to_delete = []
        for project_id in openstack_projects:
            if incremental:
                servers_to_delete.extend(
                    self._calculate_servers_to_delete_incremental(
                        openstack_projects[project_id]["servers"]
                    )
                )
            else:
                servers_to_delete.extend(
                    self._calculate_servers_to_delete(
                        openstack_projects[project_id]["servers"],
                        project_id,
                        ralph_projects,
                    )
                )
        return servers_to_delete

    def perform_delete(
        self,
        openstack_projects,
        openstack_flavors,
        ralph_projects,
        ralph_flavors,
        servers_to_delete,
    ):
        """
        Remove servers that don't exist in openstack from ralph (servers to
        delete have to be determined outside of this function).
        Remove all projects and flavors that don't exist in openstack from
        ralph.
        """
        self._delete_servers(servers_to_delete)
        for project_id in set(ralph_projects.keys()) - set(openstack_projects.keys()):
            cloud_project = CloudProject.objects.get(
                project_id=project_id, cloudprovider=self.cloud_provider
            )
            if not cloud_project:
                continue
            children_count = cloud_project.children.count()
            logger_extras = {
                "cloud_project_name": cloud_project.name,
                "cloud_project_id": cloud_project.id,
            }
            if children_count == 0:
                self._delete_object(cloud_project)
                logger.debug(
                    "Deleted Cloud Project (name: {}, id: {})".format(
                        cloud_project.name,
                        cloud_project.id,
                    ),
                    extra=logger_extras,
                )
                self.summary["del_projects"] += 1
            else:
                logger.error(
                    "Cloud project name: %s id: %s cant't be deleted "
                    "because it has %s children",
                    cloud_project.name,
                    cloud_project.id,
                    children_count,
                    extra=logger_extras,
                )

        for del_flavor in set(ralph_flavors) - set(openstack_flavors):
            flavor = CloudFlavor.objects.get(flavor_id=del_flavor)
            assignment_count = flavor.cloudhost_set.count()
            if assignment_count:
                logger_extras = {
                    "cloud_flavor_name": flavor.name,
                    "cloud_flavor_id": flavor.flavor_id,
                }
                logger.error(
                    "Cloud flavor name: %s id: %s cant't be deleted "
                    "because it is assigned to %s cloud hosts.",
                    flavor.name,
                    flavor.flavor_id,
                    assignment_count,
                    extra=logger_extras,
                )
            else:
                self._delete_object(CloudFlavor.objects.get(flavor_id=del_flavor))
                self.summary["del_flavors"] += 1

    @staticmethod
    def _save_object(obj, comment):
        """Save an object and create revision"""
        logger.info("Saving {} (id: {}; {})".format(obj, obj.id, comment))
        with transaction.atomic(), revisions.create_revision():
            obj.save()
            revisions.set_comment(comment)

    @staticmethod
    def _delete_object(obj):
        """Save an object and delete revision"""
        logger.warning("Deleting %s (id: %s)", obj, obj.id)
        with transaction.atomic(), revisions.create_revision():
            obj.delete()
            revisions.set_comment("openstack_sync::_delete_object")

    def print_summary(self, stdout):
        """
        Print sync summary
        Python 3.6 raises KeyError when using .format(**self.summary) for a
        nonexistent key. A nonexistent key has to be specified explicitly for
        defaultdict to work as expected.
        """
        msg = """
        Openstack projects synced

        Synchronization type:   {summary[sync_type]}

        New projects:           {summary[new_projects]}
        Modified projects:      {summary[mod_projects]}
        Deleted projects:       {summary[del_projects]}
        Total projects:         {summary[total_projects]}

        New instances:          {summary[new_instances]}
        Modified instances:     {summary[mod_instances]}
        Deleted instances:      {summary[del_instances]}
        Total instances:        {summary[total_instances]}

        New flavors:            {summary[new_flavors]}
        Modified flavors:       {summary[mod_flavors]}
        Deleted flavors:        {summary[del_flavors]}
        Total flavors:          {summary[total_flavors]}
        """.format(summary=self.summary)

        stdout.write(msg)
        logger.info(msg)


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--provider",
            help="OpenStack provider name",
            default=DEFAULT_OPENSTACK_PROVIDER_NAME,
        )
        parser.add_argument(
            "--match-ironic-physical-hosts",
            action="store_true",
            help="Match physical hosts and baremetal instances",
        )
        parser.add_argument(
            "--node-serial-number-parameter",
            type=str,
            default="serial_number",
            help="Extra parameter used to store node serial numbers in Ironic",
        )
        parser.add_argument(
            "--asset-serial-number-parameter",
            type=str,
            default="sn",
            help="Parameter used to store asset serial numbers in Ralph",
        )
        parser.add_argument(
            "--changes-since",
            type=int,
            default=0,
            help="Synchronize only most recent changes. Specify number of "
            "minutes to go back in time. 0 means synchronize everything.",
        )

    def handle(self, *args, **options):
        try:
            if not hasattr(settings, "OPENSTACK_INSTANCES"):
                logger.error("Nothing to sync")
                return
            logger.info("Openstack sync started...")
            match_ironic = options["match_ironic_physical_hosts"]
            openstack_provider_name = options["provider"]
            ironic_serial_number_param = options["node_serial_number_parameter"]
            ralph_serial_number_param = options["asset_serial_number_parameter"]
            changes_since = options["changes_since"]
            openstack_search_options = None
            if changes_since:
                openstack_search_options = {
                    "changes-since": datetime.now() - timedelta(minutes=changes_since)
                }

            # Fetch data from Openstack
            openstack = RalphOpenStackInfrastructureClient(openstack_provider_name)
            openstack_flavors = openstack.get_openstack_flavors()
            openstack_projects = openstack.get_openstack_projects()
            openstack_projects, openstack_flavors = (
                openstack.get_openstack_instances_data(
                    openstack_projects, openstack_flavors, openstack_search_options
                )
            )

            # Fetch data from Ralph
            ralph = RalphClient(
                openstack_provider_name,
                ironic_serial_number_param,
                ralph_serial_number_param,
                changes_since,
            )
            ralph_projects = ralph.get_ralph_projects()
            ralph_flavors = ralph.get_ralph_flavors()
            ralph_projects = ralph.get_ralph_servers_data(ralph_projects)

            # Add and update data in Ralph
            ralph.perform_update(
                openstack_projects, openstack_flavors, ralph_projects, ralph_flavors
            )
            if match_ironic:
                ralph.match_physical_and_cloud_hosts()

            # Delete data in Ralph
            servers_to_delete = ralph.calculate_servers_to_delete(
                openstack_projects, ralph_projects, incremental=bool(changes_since)
            )
            ralph.perform_delete(
                openstack_projects,
                openstack_flavors,
                ralph_projects,
                ralph_flavors,
                servers_to_delete,
            )

            # Print summary
            ralph.print_summary(self.stdout)
        except Exception as err:
            logger.exception("Openstack sync failed with error: {}".format(err))
