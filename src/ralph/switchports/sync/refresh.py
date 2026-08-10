"""Refresh validation results from the netmaker backend.

Fetches switch port data from netmaker for each switch related to a
RackConfiguration (both the switches configured on the columns and the
per-server override switches), uses netmaker asset matching to resolve the
remote asset, and caches the results in BackendValidationResult.
"""

import logging

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.constants import SWITCH_SENTINEL_LABEL
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    ValidationStatus,
)
from ralph.switchports.netmaker import SwitchDTO
from ralph.switchports.netmaker.asset_matching import cross_validate, extract_asset
from ralph.switchports.netmaker.backend import (
    NetmakerSwitchportBackend,
    SwitchportSyncBackend,
)
from ralph.switchports.netmaker.lldp import RemoteAsset
from ralph.switchports.sync.port_sync import sync_switch_ports
from ralph.switchports.sync.switches import (
    disabled_only_switch_ids,
    iter_rack_switches,
)

logger = logging.getLogger(__name__)


def refresh_validation_for_rack(
    rack_configuration: RackConfiguration,
    *,
    trigger_backend_refresh: bool = False,
) -> dict:
    """Refresh netmaker validation for all switches related to a rack.

    Runs synchronously. The async grid button uses ``ralph.switchports.sync.tasks``
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

    stale_switch_ids = disabled_only_switch_ids(rack_configuration)
    if stale_switch_ids:
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
        rebuild_validation_for_switch(backend, switch, summary)

    return summary


def rebuild_validation_for_switch(
    backend: SwitchportSyncBackend,
    switch: DataCenterAsset,
    summary: dict,
) -> None:
    """Pull fresh ports for a single switch and rebuild its validation cache.

    Also reconciles the switch's Ports with the backend: the backend is the
    source of truth for which switch ports exist, so missing ports are created
    and vanished ones are deleted (unless they still take part in a connection,
    in which case they are kept — see ``sync.port_sync``).
    """
    try:
        switch_dto = backend.get_switchports(switch.hostname)
    except Exception:
        logger.warning(
            "Failed to fetch switchports from backend for %s",
            switch.hostname,
            exc_info=True,
        )
        # Mark this switch as not found in the backend.
        BackendValidationResult.objects.filter(
            switch=switch,
        ).delete()
        BackendValidationResult.objects.create(
            switch=switch,
            port_label=SWITCH_SENTINEL_LABEL,
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
    sync_switch_ports(
        switch,
        {interface.name for interface in switch_dto.ports},
        summary,
    )

    # Delete old results for this switch and rebuild
    BackendValidationResult.objects.filter(
        switch=switch,
    ).delete()

    results_to_create = _backend_validation_results_to_create(switch, switch_dto)
    if results_to_create:
        BackendValidationResult.objects.bulk_create(results_to_create)
        summary["ports_processed"] += len(results_to_create)


def _backend_validation_results_to_create(
    switch: DataCenterAsset, switch_dto: SwitchDTO
) -> list[BackendValidationResult]:
    results_to_create = []
    for interface in switch_dto.ports:
        port_label = interface.name
        remote = RemoteAsset.from_interface_dto(interface)
        asset_from_name, asset_from_desc, asset_from_mac = extract_asset(remote)

        if (
            is_consistent := cross_validate(asset_from_name, asset_from_desc, asset_from_mac)
        ) is not None:
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
            remote.remote_hostname_from_remote_name or remote.remote_hostname_from_desc or ""
        )

        results_to_create.append(
            BackendValidationResult(
                switch=switch,
                port_label=port_label,
                status=status,
                remote_asset=resolved_asset,
                remote_hostname=remote_hostname,
                oper_status=interface.status.value if interface.status else "",
                admin_status=(interface.admin_status.value if interface.admin_status else ""),
                speed=interface.speed,
                raw_data=interface.model_dump(mode="json"),
            )
        )
    return results_to_create
