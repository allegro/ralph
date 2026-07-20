import re

from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from ralph.admin.views.extra import RalphDetailView
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import BackendValidationResult, ConnectionMember, Port
from ralph.switchports.presentation import build_validation_context
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

    def _self_switch_validation_map(self):
        """netmaker results where THIS asset is the switch, keyed by port label."""
        results = BackendValidationResult.objects.filter(
            switch=self.object
        ).select_related("remote_asset")
        return {vr.port_label: vr for vr in results if vr.port_label != "__switch__"}

    def _remote_switch_validation_map(self, remote_asset_ids):
        """netmaker results where the REMOTE asset is the switch.

        Keyed by (switch_id, port_label) so we can look up what netmaker reports
        on the switch side of a connection when this asset is a server.
        """
        if not remote_asset_ids:
            return {}
        results = BackendValidationResult.objects.filter(
            switch_id__in=remote_asset_ids
        ).select_related("remote_asset")
        return {
            (vr.switch_id, vr.port_label): vr
            for vr in results
            if vr.port_label != "__switch__"
        }

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

        ports = sorted(ports, key=_natural_port_sort_key)

        # Resolve remote side for every port up-front.
        remote_by_port = {}
        remote_asset_ids = set()
        for port in ports:
            connection_member = getattr(port, "connectionmember", None)
            if not connection_member:
                continue
            for member in connection_member.connection.members.all():
                if member.port_id != port.id:
                    remote_by_port[port.id] = (
                        member.port,
                        member.port.data_center_asset,
                    )
                    if member.port.data_center_asset_id:
                        remote_asset_ids.add(member.port.data_center_asset_id)
                    break

        self_switch_map = self._self_switch_validation_map()
        remote_switch_map = self._remote_switch_validation_map(remote_asset_ids)

        ports_data = []
        for port in ports:
            remote_port, remote_asset = remote_by_port.get(port.id, (None, None))

            # Prefer netmaker data for this asset's own port (asset acts as switch);
            # otherwise fall back to what the remote switch reports for this link.
            validation = None
            vr_self = self_switch_map.get(port.label)
            if vr_self is not None:
                expected_id = remote_asset.id if remote_asset else None
                validation = build_validation_context(
                    vr_self, expected_asset_id=expected_id
                )
            elif remote_asset is not None and remote_port is not None:
                vr_remote = remote_switch_map.get((remote_asset.id, remote_port.label))
                validation = build_validation_context(
                    vr_remote, expected_asset_id=self.object.id
                )

            ports_data.append(
                {
                    "port": port,
                    "remote_port": remote_port,
                    "remote_asset": remote_asset,
                    "validation": validation,
                }
            )

        context["ports_data"] = ports_data
        return context
