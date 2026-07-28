"""Per-server switch overrides: the "this server is wired differently" edge case.

A column (``RackSwitchConfiguration``) defines the default switch for every
server in the rack. An override lets one server point its column port at a
different switch. These helpers answer "which switch does this cell really use"
and keep the override rows in sync when the grid is saved.
"""

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import (
    RackSwitchConfigurationOverride,
    RackSwitchConfiguration,
)


def build_override_map(switch_configs) -> dict:
    """Map ``(asset_id, switch_config_id) -> override switch`` (DataCenterAsset)."""
    sc_ids = [sc.id for sc in switch_configs]
    override_map: dict = {}
    if not sc_ids:
        return override_map
    overrides = RackSwitchConfigurationOverride.objects.filter(
        rack_switch_configuration_id__in=sc_ids
    ).select_related("switch")
    for override in overrides:
        override_map[
            (override.data_center_asset_id, override.rack_switch_configuration_id)
        ] = override.switch
    return override_map


def effective_switch(
    sc: RackSwitchConfiguration,
    asset_id: int,
    override_map: dict[tuple[int, int], DataCenterAsset],
) -> DataCenterAsset:
    """The switch an asset connects to for a column (override or default)."""
    return override_map.get((asset_id, sc.id)) or sc.switch


def sync_override(
    sc, asset: DataCenterAsset, target_switch: DataCenterAsset, override_value
) -> None:
    """Create, update or drop the per-server override for a cell.

    An override is only kept when the user supplied one *and* it actually
    differs from the column default; otherwise any existing override is removed.
    """
    if override_value and target_switch.id != sc.switch_id:
        RackSwitchConfigurationOverride.objects.update_or_create(
            rack_switch_configuration=sc,
            data_center_asset=asset,
            defaults={"switch": target_switch},
        )
    else:
        RackSwitchConfigurationOverride.objects.filter(
            rack_switch_configuration=sc,
            data_center_asset=asset,
        ).delete()
