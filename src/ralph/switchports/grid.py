"""Build the switchport grid model (rows x switch-column cells).

Pure functions with no HTTP coupling so the grid can be unit-tested directly.
The Django view (`views.RackSwitchportGridView`) just wires these together and
renders the result. Each function owns one lookup, and the per-cell edge cases
(override switch, SWITCH_NOT_FOUND sentinel, PORT_NOT_FOUND fallback, display
label stripping) are assembled in ``build_grid_rows``.
"""

from typing import Iterable


from ralph.data_center.models import DataCenterAsset
from ralph.switchports.constants import (
    SWITCH_SENTINEL_LABEL,
    grid_force_field,
    grid_override_field,
    grid_port_field,
)
from ralph.switchports.models import (
    BackendValidationResult,
    Port,
    RackConfiguration,
    ValidationStatus,
    RackSwitchConfiguration,
)
from ralph.switchports.presentation import build_validation_context
from ralph.switchports.rackconfig.overrides import effective_switch
from ralph.switchports.rackconfig.port_labels import to_display
from ralph.switchports.sync import iter_rack_switches


def get_rack_assets(rack) -> Iterable[DataCenterAsset]:
    """All DataCenterAssets in this rack, ordered like the grid renders them."""
    return (
        DataCenterAsset.objects.filter(rack=rack)
        .select_related("model", "model__category")
        .order_by("-position", "slot_no", "hostname")
    )


def get_switch_configs(
    rack_configuration: RackConfiguration,
) -> Iterable[RackSwitchConfiguration]:
    """All RackSwitchConfigurations (columns) for this rack, ordered by label."""
    return rack_configuration.switches.select_related("switch").order_by("label")


def build_connection_map(assets, switch_configs) -> dict:
    """Map ``(asset_id, switch_config_id) -> port info`` for existing links.

    Matches an asset's port to a column by label, then records the switch port
    it is connected to and which switch that actually is (which may be an
    override switch rather than the column default). A remote member is treated
    as the switch side only when it is a *different* asset than the local one.
    """
    label_to_sc = {sc.label: sc for sc in switch_configs}
    asset_ids = [a.id for a in assets]

    if not asset_ids or not label_to_sc:
        return {}

    asset_ports = (
        Port.objects.filter(
            data_center_asset_id__in=asset_ids,
            label__in=list(label_to_sc.keys()),
        )
        .select_related(
            "connectionmember__connection",
        )
        .prefetch_related(
            "connectionmember__connection__members__port__data_center_asset",
        )
    )

    connection_map = {}
    for port in asset_ports:
        sc = label_to_sc.get(port.label)
        if sc is None:
            continue
        conn_member = getattr(port, "connectionmember", None)
        if not conn_member:
            continue
        connection = conn_member.connection
        for member in connection.members.all():
            if member.port_id == port.id:
                continue
            remote_port = member.port
            remote_asset = remote_port.data_center_asset
            # Only treat the remote as a switch cell if it is not the local
            # asset itself (heuristic: it is a switch if it differs).
            if remote_asset.id == port.data_center_asset_id:
                continue
            connection_map[(port.data_center_asset_id, sc.id)] = {
                "switch_port_label": remote_port.label,
                "asset_port_label": port.label,
                "actual_switch_id": remote_asset.id,
            }
    return connection_map


def build_validation_map(rack_configuration: RackConfiguration) -> tuple[dict, dict]:
    """Return ``(validation_map, switch_status)`` for a rack.

    ``validation_map`` is keyed by ``(switch_id, port_label)``; ``switch_status``
    carries the per-switch sentinel status (e.g. SWITCH_NOT_FOUND) for switches
    that reported one.
    """
    switches = iter_rack_switches(rack_configuration)
    results = BackendValidationResult.objects.filter(
        switch__in=switches
    ).select_related("remote_asset")

    validation_map = {}
    switch_status = {}
    for result in results:
        if result.port_label == SWITCH_SENTINEL_LABEL:
            switch_status[result.switch_id] = result.status
        else:
            validation_map[(result.switch_id, result.port_label)] = result

    return validation_map, switch_status


def build_client_validation(switch_configs, validation_map, switch_status) -> dict:
    """Serialize default-switch validation for instant, client-side checks.

    Only default (non-override) switches are included: the grid preloads every
    validated port so typing a port number gives immediate feedback without any
    AJAX. Overrides and backend-validation-disabled columns are excluded.
    """
    client = {}
    for sc in switch_configs:
        if not sc.backend_validation:
            continue
        ports = {}
        for (switch_id, port_label), vr in validation_map.items():
            if switch_id != sc.switch_id:
                continue
            ports[port_label] = {
                "status": vr.status,
                "remote_asset_id": vr.remote_asset_id,
                "remote_hostname": vr.remote_hostname,
            }
        client[str(sc.id)] = {
            "switch_not_found": sc.switch_id in switch_status,
            "ports": ports,
        }
    return client


def _cell_validation(
    sc: RackSwitchConfiguration,
    effective_switch_obj: DataCenterAsset,
    switch_port_label: str,
    asset_id: int,
    validation_map: dict[tuple[int, str], BackendValidationResult],
    switch_status,
    has_validation,
):
    """Resolve the netmaker validation badge for a single grid cell."""
    if not sc.backend_validation:
        # Backend validation disabled: no netmaker column for this switch.
        return None
    if not switch_port_label:
        return None
    if effective_switch_obj.id in switch_status:
        return {
            "status": ValidationStatus.SWITCH_NOT_FOUND,
            "css_class": "validation-error",
            "label": "SWITCH N/F",
        }
    vr: BackendValidationResult | None = validation_map.get(
        (effective_switch_obj.id, switch_port_label)
    )
    if vr is not None:
        return build_validation_context(vr, expected_asset_id=asset_id)
    if has_validation:
        return {
            "status": ValidationStatus.PORT_NOT_FOUND,
            "css_class": "validation-warning",
            "label": "PORT N/F",
        }
    return None


def build_grid_rows(
    assets: Iterable[DataCenterAsset],
    switch_configs,
    override_map,
    connection_map,
    validation_map,
    switch_status,
    has_validation,
    conflicts=None,
) -> list[dict]:
    """Assemble the full grid: one row per asset, one cell per switch column.

    ``conflicts`` (``{(asset_id, sc_id): conflict_payload}``) marks cells whose
    last edit was a rejected port steal: those render the user's typed value
    plus an "overwrite" checkbox instead of the saved connection.
    """
    conflicts = conflicts or {}
    rows = []
    for asset in assets:
        cells = []
        for sc in switch_configs:
            conflict = conflicts.get((asset.id, sc.id))
            if conflict is not None:
                cells.append(_conflict_cell(asset, sc, conflict))
                continue

            effective_switch_obj = effective_switch(sc, asset.id, override_map)
            override_switch = override_map.get((asset.id, sc.id))
            conn_info = connection_map.get((asset.id, sc.id))
            if conn_info:
                switch_port_label = conn_info["switch_port_label"]
                display_value = to_display(switch_port_label)
            else:
                switch_port_label = None
                display_value = ""

            cells.append(
                {
                    "switch_config": sc,
                    "value": display_value,
                    "field_name": grid_port_field(asset.id, sc.id),
                    "override_field_name": grid_override_field(asset.id, sc.id),
                    "force_field_name": grid_force_field(asset.id, sc.id),
                    "override_value": (
                        (override_switch.barcode or override_switch.hostname)
                        if override_switch
                        else ""
                    ),
                    "is_override": bool(override_switch),
                    "is_conflict": False,
                    "validation": _cell_validation(
                        sc,
                        effective_switch_obj,
                        switch_port_label,
                        asset.id,
                        validation_map,
                        switch_status,
                        has_validation,
                    ),
                    "port_label_proposal": _propose_port(asset, effective_switch_obj),
                }
            )
        rows.append({"asset": asset, "cells": cells})
    return rows


def _propose_port(asset: DataCenterAsset, switch: DataCenterAsset) -> str | None:
    port_proposals = BackendValidationResult.objects.filter(
        switch=switch, remote_asset=asset
    )
    if port_proposals:
        return " ".join([p.port_label for p in port_proposals])
    return None


def _conflict_cell(asset, sc, conflict) -> dict:
    """A cell whose edit was rejected: show the typed value + overwrite toggle."""
    return {
        "switch_config": sc,
        "value": conflict["typed_value"],
        "field_name": grid_port_field(asset.id, sc.id),
        "override_field_name": grid_override_field(asset.id, sc.id),
        "force_field_name": grid_force_field(asset.id, sc.id),
        "override_value": conflict["typed_override"],
        "is_override": bool(conflict["typed_override"]),
        "is_conflict": True,
        "conflict_owner": conflict["owner_barcode"],
        "conflict_switch": conflict["switch_hostname"],
        "conflict_port": conflict["switch_port_label"],
        "validation": None,
    }
