"""Reconcile a switch's Ports with what the backend reports.

The backend (netmaker) is the source of truth for which ports physically exist
on a switch. This module owns the two edge cases that governs:

* ports the backend reports but Ralph is missing are **created**;
* ports Ralph has but the backend no longer reports are **deleted** — *unless*
  the port still takes part in a Connection, in which case it is **kept** so the
  connection (and the server port on the other side) survives.

Server ports and connections are never created here.
"""

from django.db import transaction

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import ConnectionMember, Port


def sync_switch_ports(
    switch: DataCenterAsset,
    backend_port_labels: set[str],
    summary: dict,
) -> None:
    """Make the switch's Ports match ``backend_port_labels``.

    See the module docstring for the create / delete / keep-connected rules.
    """
    existing_ports = {
        port.label: port
        for port in Port.objects.filter(data_center_asset=switch)
    }
    existing_labels = set(existing_ports)

    labels_to_create = backend_port_labels - existing_labels
    labels_to_delete = existing_labels - backend_port_labels

    with transaction.atomic():
        if labels_to_delete:
            _delete_unconnected_ports(
                [existing_ports[label] for label in labels_to_delete], summary
            )
        if labels_to_create:
            Port.objects.bulk_create(
                [
                    Port(label=label, data_center_asset=switch)
                    for label in labels_to_create
                ]
            )
            summary["switch_ports_created"] = (
                summary.get("switch_ports_created", 0) + len(labels_to_create)
            )


def _delete_unconnected_ports(candidate_ports: list[Port], summary: dict) -> None:
    """Delete only the candidate ports that have no Connection.

    A port that still participates in a Connection is kept so its connection
    (and the server port on the other side) is never torn down here.
    """
    connected_port_ids = set(
        ConnectionMember.objects.filter(
            port__in=candidate_ports
        ).values_list("port_id", flat=True)
    )
    ports_to_delete = [
        port for port in candidate_ports if port.id not in connected_port_ids
    ]
    if not ports_to_delete:
        return
    Port.objects.filter(id__in=[port.id for port in ports_to_delete]).delete()
    summary["switch_ports_deleted"] = (
        summary.get("switch_ports_deleted", 0) + len(ports_to_delete)
    )
