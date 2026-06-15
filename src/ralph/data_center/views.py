import re

from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from ralph.admin.views.extra import RalphDetailView
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import ConnectionMember, Port
from ralph.virtual.models import VirtualServer


def _natural_port_sort_key(port):
    """Sort port labels numerically by segments.

    Splits label by '/' and ':' separators, converting numeric parts to ints.
    E.g. "0/0/2" < "0/0/19" < "0/0/48:0" < "0/0/48:1"
    """
    parts = re.split(r"[/:]", port.label)
    key = []
    for part in parts:
        try:
            key.append((0, int(part)))
        except ValueError:
            key.append((1, part))
    return key


class RelationsView(RalphDetailView):
    icon = "shekel"
    label = "Relations"
    name = "relations"
    url_name = "relations"
    template_name = "data_center/datacenterasset/relations.html"

    def _add_cloud_hosts(self, related_objects):
        cloud_hosts = list(self.object.cloudhost_set.all())

        if cloud_hosts:
            related_objects["cloud_hosts"] = cloud_hosts

    def _add_virtual_hosts(self, related_objects):
        virtual_server = ContentType.objects.get_for_model(VirtualServer)
        virtual_hosts = list(self.object.children.filter(content_type=virtual_server))

        if virtual_hosts:
            related_objects["virtual_hosts"] = virtual_hosts

    def _add_physical_hosts(self, related_objects):
        physical_server = ContentType.objects.get_for_model(DataCenterAsset)
        physical_hosts = list(self.object.children.filter(content_type=physical_server))

        if physical_hosts:
            related_objects["physical_hosts"] = physical_hosts

    def _add_clusters(self, related_objects):
        clusters = [
            base_object.cluster for base_object in list(self.object.clusters.all())
        ]

        if clusters:
            related_objects["clusters"] = clusters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_objects = {}
        self._add_cloud_hosts(related_objects)
        self._add_virtual_hosts(related_objects)
        self._add_physical_hosts(related_objects)
        self._add_clusters(related_objects)
        context["related_objects"] = related_objects

        return context


class PortsView(RalphDetailView):
    icon = "plug"
    label = "Ports"
    name = "ports"
    url_name = "ports"
    template_name = "data_center/datacenterasset/ports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ports = (
            Port.objects.filter(data_center_asset=self.object)
            .select_related("connectionmember__connection")
            .prefetch_related(
                Prefetch(
                    "connectionmember__connection__members",
                    queryset=ConnectionMember.objects.select_related(
                        "port__data_center_asset"
                    ),
                )
            )
        )

        ports_data = []
        for port in sorted(ports, key=_natural_port_sort_key):
            remote_port = None
            remote_asset = None
            connection_member = getattr(port, "connectionmember", None)
            if connection_member:
                connection = connection_member.connection
                for member in connection.members.all():
                    if member.port_id != port.id:
                        remote_port = member.port
                        remote_asset = member.port.data_center_asset
                        break

            ports_data.append(
                {
                    "port": port,
                    "remote_port": remote_port,
                    "remote_asset": remote_asset,
                }
            )

        context["ports_data"] = ports_data
        return context
