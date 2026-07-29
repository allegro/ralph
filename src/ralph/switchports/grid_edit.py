"""Apply a single switchport grid cell edit (the grid's write model).

Complements ``grid`` (the read model that builds what is shown). The one edge
case that lives here is the **conflict gate**: an edit whose target switch port
is already used by another asset is *not* applied unless it is explicitly
``forced``. That is what turns a silent port steal into an intentional,
user-confirmed reassignment.
"""

from dataclasses import dataclass

from ralph.switchports.connections import connect, disconnect, switch_port_owner
from ralph.switchports.models import Port
from ralph.switchports.rackconfig.overrides import sync_override
from ralph.switchports.rackconfig.port_labels import to_switch_label
from ralph.switchports.rackconfig.switch_resolver import resolve_switch


@dataclass
class CellEdit:
    """The user's raw input for one grid cell."""

    new_value: str = ""
    override_value: str = ""
    forced: bool = False


@dataclass
class CellResult:
    """Outcome of applying one cell.

    Exactly one of the meaningful states is set: a count (created/removed), an
    ``error`` string, or a ``conflict`` payload describing a deferred steal.
    """

    created: int = 0
    removed: int = 0
    error: str | None = None
    conflict: dict | None = None


def apply_cell_edit(asset, sc, edit: CellEdit, connection_map, dc) -> CellResult:
    """Reconcile one grid cell for ``asset`` in column ``sc``.

    Ordering matters: the conflict gate runs *before* anything is written, so a
    rejected conflict leaves both the override and the existing connection
    untouched.
    """
    new_value = (edit.new_value or "").strip()
    override_value = (edit.override_value or "").strip()

    # Resolve the target switch (override or column default).
    if override_value:
        target_switch = resolve_switch(override_value, dc)
        if target_switch is None:
            return CellResult(
                error=f"{asset.hostname} / {sc.label}: "
                f"unknown switch '{override_value}'"
            )
    else:
        target_switch = sc.switch

    new_label = to_switch_label(new_value) if new_value else None

    # Conflict gate: the target port is already used by a *different* asset.
    # Defer the whole cell (override included) until the user confirms.
    if new_label and not edit.forced:
        owner = switch_port_owner(target_switch, new_label, asset)
        if owner is not None:
            return CellResult(
                conflict={
                    "typed_value": new_value,
                    "typed_override": override_value,
                    "owner_hostname": owner.hostname,
                    "owner_barcode": owner.barcode,
                    "owner_sn": owner.sn,
                    "switch_hostname": target_switch.hostname,
                    "switch_port_label": new_label,
                }
            )

    # Persist the override choice (independent of the connection itself).
    sync_override(sc, asset, target_switch, override_value)

    existing = connection_map.get((asset.id, sc.id))
    existing_label = existing["switch_port_label"] if existing else None
    existing_switch_id = existing["actual_switch_id"] if existing else None

    unchanged = existing_label == new_label and existing_switch_id == (
        target_switch.id if new_label else None
    )
    if unchanged:
        return CellResult()

    if existing and not new_label:
        # Cleared cell -> disconnect the asset's own port.
        try:
            asset_port = Port.objects.get(
                label=existing["asset_port_label"],
                data_center_asset=asset,
            )
            disconnect(asset_port)
            return CellResult(removed=1)
        except Port.DoesNotExist:
            return CellResult()

    if new_label:
        # Connect (or reconnect, possibly to a different switch). The gate above
        # guarantees this only steals a used port when ``forced`` is set.
        try:
            asset_port, _ = Port.objects.get_or_create(
                label=sc.label,
                data_center_asset=asset,
            )
            switch_port, _ = Port.objects.get_or_create(
                label=new_label,
                data_center_asset=target_switch,
            )
            connect(asset_port, switch_port)
            return CellResult(created=1)
        except Exception as e:
            return CellResult(error=f"{asset.hostname} / {sc.label}: {e}")

    return CellResult()
