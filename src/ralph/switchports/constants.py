"""Cross-cutting switchport constants.

Magic values that used to be duplicated inline across views, validation and the
data-center Ports tab live here, so an edge case has exactly one definition.
"""

# BackendValidationResult sentinel: a row with this ``port_label`` carries the
# *per-switch* status (e.g. SWITCH_NOT_FOUND) instead of a real port result.
SWITCH_SENTINEL_LABEL = "__switch__"

# A switch port entered as a bare number (``20``) is stored as ``0/0/20``.
DEFAULT_SWITCH_PORT_PREFIX = "0/0/"

# Async (RQ) rack refresh: queue name and tuning defaults. The concrete values
# are overridable via settings (see settings.base ``SWITCHPORT_REFRESH_*``).
REFRESH_QUEUE_NAME = "ralph_switchports"
DEFAULT_MAX_PARALLEL = 4
DEFAULT_LOCK_TIMEOUT = 300
DEFAULT_LOCK_BLOCKING_TIMEOUT = 120


def grid_port_field(asset_id: int, switch_config_id: int) -> str:
    """POST field name holding the switch port for one grid cell."""
    return f"port_{asset_id}_{switch_config_id}"


def grid_override_field(asset_id: int, switch_config_id: int) -> str:
    """POST field name holding the override switch for one grid cell."""
    return f"override_{asset_id}_{switch_config_id}"


def grid_force_field(asset_id: int, switch_config_id: int) -> str:
    """POST field name (checkbox) confirming an overwrite of a used switch port.

    Present in POST only when the user ticked "overwrite" for that cell, which
    is what turns a rejected conflict into an intentional, destructive reassign.
    """
    return f"force_{asset_id}_{switch_config_id}"
