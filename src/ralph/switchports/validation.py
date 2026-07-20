"""Refresh validation results from the netmaker backend.

Fetches switch port data from netmaker for each switch related to a
RackConfiguration (both the switches configured on the columns and the
per-server override switches), uses asset_matching.extract_asset to resolve the
remote asset, and caches the results in BackendValidationResult.
"""

import logging

from django.db import transaction

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.asset_matching import RemoteAsset, extract_asset, cross_validate
from ralph.switchports.backend import NetmakerSwitchportBackend
from ralph.switchports.models import (
    BackendValidationResult,
    ConnectionMember,
    Port,
    RackConfiguration,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


def iter_rack_switches(rack_configuration: RackConfiguration) -> list[DataCenterAsset]:
    """Return the deduplicated switches related to a rack.

    Includes every switch configured on a column that has backend validation
    enabled, plus every per-server override switch defined on such columns.
    This is the set of switches that a netmaker refresh must cover.
    """
    switches: dict[int, DataCenterAsset] = {}
    switch_configs = rack_configuration.switches.filter(
        backend_validation=True
    ).select_related("switch").prefetch_related("overrides__switch")
    for sc in switch_configs:
        switches.setdefault(sc.switch_id, sc.switch)
        for override in sc.overrides.all():
            switches.setdefault(override.switch_id, override.switch)
    return list(switches.values())


def _disabled_only_switch_ids(rack_configuration: RackConfiguration) -> set[int]:
    """Switch ids referenced *only* by backend-validation-disabled columns.

    Their stale cached results should be dropped on refresh.
    """
    enabled_ids: set[int] = {s.id for s in iter_rack_switches(rack_configuration)}
    disabled_ids: set[int] = set()
    for sc in rack_configuration.switches.filter(
        backend_validation=False
    ).select_related("switch").prefetch_related("overrides"):
        disabled_ids.add(sc.switch_id)
        disabled_ids.update(sc.overrides.values_list("switch_id", flat=True))
    return disabled_ids - enabled_ids


def refresh_validation_for_rack(
    rack_configuration: RackConfiguration,
    *,
    trigger_backend_refresh: bool = False,
) -> dict:
    """Refresh netmaker validation for all switches related to a rack.

    Runs synchronously. The async grid button uses ``ralph.switchports.tasks``
    instead; this helper stays available for the management command and tests.

    Returns a summary dict with counts of results per status.
    """
    backend = NetmakerSwitchportBackend()
    summary = {
        "refreshed_switches": 0,
        "switch_not_found": 0,
        "ports_processed": 0,
        "skipped_switches": 0,
    }

    # Drop stale results for switches that are no longer validated.
    stale_switch_ids = _disabled_only_switch_ids(rack_configuration)
    if stale_switch_ids:
        BackendValidationResult.objects.filter(
            rack_configuration=rack_configuration,
            switch_id__in=stale_switch_ids,
        ).delete()
        summary["skipped_switches"] = len(stale_switch_ids)

    for switch in iter_rack_switches(rack_configuration):
        if trigger_backend_refresh:
            try:
                backend.refresh_switch(switch.hostname)
            except Exception:
                logger.warning(
                    "Failed to trigger backend refresh for %s",
                    switch.hostname,
                    exc_info=True,
                )
        rebuild_validation_for_switch(
            backend,
            rack_configuration,
            switch,
            summary
        )

    return summary


def _sync_switch_ports(
    switch: DataCenterAsset,
    backend_port_labels: set[str],
    summary: dict,
) -> None:
    """Make the switch's Ports match what the backend reports.

    The backend is the source of truth for which ports physically exist on a
    switch. Ports reported by the backend but missing in Ralph are created;
    Ralph ports no longer reported by the backend are deleted. A port that
    still takes part in a Connection is never deleted, so no existing
    connection (or the server port on the other side) is ever torn down here.

    Server ports and connections are never created here.
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
            candidate_ports = [existing_ports[label] for label in labels_to_delete]
            # Never delete a port that still participates in a Connection. Such
            # a port is kept so its Connection (and the server port on the other
            # side) survives, even though the backend no longer reports it.
            connected_port_ids = set(
                ConnectionMember.objects.filter(
                    port__in=candidate_ports
                ).values_list("port_id", flat=True)
            )
            ports_to_delete = [
                port for port in candidate_ports if port.id not in connected_port_ids
            ]
            if ports_to_delete:
                Port.objects.filter(
                    id__in=[port.id for port in ports_to_delete]
                ).delete()
                summary["switch_ports_deleted"] = (
                    summary.get("switch_ports_deleted", 0) + len(ports_to_delete)
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


def rebuild_validation_for_switch(
    backend,
    rack_configuration: RackConfiguration,
    switch: DataCenterAsset,
    summary: dict,
) -> None:
    """Pull fresh ports for a single switch and rebuild its validation cache.

    Also reconciles the switch's Ports with the backend: the backend is the
    source of truth for which switch ports exist, so missing ports are created
    and vanished ones are deleted (unless they still take part in a connection,
    in which case they are kept).
    """
    try:
        switch_dto = backend.get_switchports(
            switch.hostname
        )
    except Exception:
        logger.warning(
            "Failed to fetch switchports from backend for %s",
            switch.hostname,
            exc_info=True,
        )
        # Mark this switch as not found in the backend.
        BackendValidationResult.objects.filter(
            rack_configuration=rack_configuration,
            switch=switch,
        ).delete()
        BackendValidationResult.objects.create(
            rack_configuration=rack_configuration,
            switch=switch,
            port_label="__switch__",
            status=ValidationStatus.SWITCH_NOT_FOUND,
            remote_hostname="",
        )
        summary["switch_not_found"] += 1
        return

    summary["refreshed_switches"] += 1

    # Reconcile the switch's ports with the backend (source of truth). Only the
    # backend fetch succeeding lets us treat a missing port as truly gone; a
    # backend hiccup takes the SWITCH_NOT_FOUND path above and leaves ports
    # untouched.
    _sync_switch_ports(
        switch,
        {interface.name for interface in switch_dto.ports},
        summary,
    )

    # Delete old results for this switch and rebuild
    BackendValidationResult.objects.filter(
        rack_configuration=rack_configuration,
        switch=switch,
    ).delete()

    results_to_create = []
    for interface in switch_dto.ports:
        port_label = interface.name
        remote = RemoteAsset.from_interface_dto(interface)
        asset_from_name, asset_from_desc, asset_from_mac = extract_asset(remote)

        if is_consistent := cross_validate(asset_from_name, asset_from_desc, asset_from_mac):
            if not is_consistent:
                resolved_asset = asset_from_name or asset_from_desc or asset_from_mac
                status = ValidationStatus.ASSET_CONFLICT
            else:
                # All agree on the same asset
                resolved_asset = asset_from_name or asset_from_desc or asset_from_mac
                status = ValidationStatus.ASSET_FOUND
        else:
            # None found
            resolved_asset = None
            status = ValidationStatus.PORT_NOT_FOUND

        remote_hostname = (
            remote.remote_hostname_from_remote_name
            or remote.remote_hostname_from_desc
            or ""
        )

        results_to_create.append(
            BackendValidationResult(
                rack_configuration=rack_configuration,
                switch=switch,
                port_label=port_label,
                status=status,
                remote_asset=resolved_asset,
                remote_hostname=remote_hostname,
                oper_status=interface.status.value if interface.status else "",
                admin_status=(
                    interface.admin_status.value if interface.admin_status else ""
                ),
                speed=interface.speed,
                raw_data=interface.model_dump(mode="json"),
            )
        )

    if results_to_create:
        BackendValidationResult.objects.bulk_create(results_to_create)
        summary["ports_processed"] += len(results_to_create)
