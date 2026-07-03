"""Refresh validation results from the netmaker backend.

Fetches switch port data from netmaker for each switch in a RackConfiguration,
uses asset_matching.extract_asset to resolve the remote asset, and caches the
results in BackendValidationResult.
"""

import logging

from ralph.switchports.asset_matching import RemoteAsset, extract_asset, cross_validate
from ralph.switchports.backend import NetmakerSwitchportBackend
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    RackSwitchConfiguration,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


def refresh_validation_for_rack(rack_configuration: RackConfiguration) -> dict:
    """Refresh netmaker validation for all switches in a rack configuration.

    Returns a summary dict with counts of results per status.
    """
    backend = NetmakerSwitchportBackend()
    switch_configs = rack_configuration.switches.select_related("switch").all()
    summary = {
        "refreshed_switches": 0,
        "switch_not_found": 0,
        "ports_processed": 0,
    }

    for sc in switch_configs:
        _refresh_switch(backend, rack_configuration, sc, summary)

    return summary


def _refresh_switch(backend, rack_configuration, sc: RackSwitchConfiguration, summary):
    """Refresh validation for a single switch."""
    switch = sc.switch

    try:
        switch_dto = backend.get_switchports(switch.hostname)
    except Exception:
        logger.warning(
            "Failed to fetch switchports from backend for %s",
            switch.hostname,
            exc_info=True,
        )
        # Mark all existing results for this switch as SWITCH_NOT_FOUND
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

        is_consistent = cross_validate(asset_from_name, asset_from_desc, asset_from_mac)

        if is_consistent is False:
            # Conflicting assets
            resolved_asset = asset_from_name or asset_from_desc or asset_from_mac
            status = ValidationStatus.ASSET_CONFLICT
        elif is_consistent is True:
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
            )
        )

    if results_to_create:
        BackendValidationResult.objects.bulk_create(results_to_create)
        summary["ports_processed"] += len(results_to_create)
