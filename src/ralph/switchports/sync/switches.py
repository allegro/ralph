"""Enumerate the switches a rack refresh must cover."""

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import RackConfiguration


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


def disabled_only_switch_ids(rack_configuration: RackConfiguration) -> set[int]:
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
