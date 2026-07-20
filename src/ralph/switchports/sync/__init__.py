"""Netmaker refresh → Ralph: switch enumeration, port reconciliation and caching.

* ``switches``  — which switches a rack refresh must cover
* ``port_sync`` — reconcile a switch's Ports with the backend (keep-connected)
* ``refresh``   — pull ports and rebuild the validation cache
* ``tasks``     — async, locked, parallel RQ entrypoint
"""

from ralph.switchports.sync.refresh import (
    rebuild_validation_for_switch,
    refresh_validation_for_rack,
)
from ralph.switchports.sync.switches import (
    disabled_only_switch_ids,
    iter_rack_switches,
)

__all__ = [
    "disabled_only_switch_ids",
    "iter_rack_switches",
    "rebuild_validation_for_switch",
    "refresh_validation_for_rack",
]
