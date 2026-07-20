"""Switch port label normalization.

A switch port typed as a bare number is stored as ``0/0/<n>``; the grid shows
it back without the default prefix. Both directions of that edge case live
here so they can never drift apart.
"""

from ralph.switchports.constants import DEFAULT_SWITCH_PORT_PREFIX


def to_switch_label(port_number: str) -> str:
    """Normalize a user-entered switch port to a full label.

    A bare number ``20`` becomes ``0/0/20``; a value already containing ``/``
    (e.g. ``1/0/5``) is treated as a full label and passes through unchanged.
    """
    port_number = (port_number or "").strip()
    if "/" in port_number:
        return port_number
    return f"{DEFAULT_SWITCH_PORT_PREFIX}{port_number}"


def to_display(port_label: str) -> str:
    """Strip the default ``0/0/`` prefix for compact grid display.

    ``0/0/42`` shows as ``42``; non-default labels (``1/0/5``) are shown as-is.
    """
    if port_label.startswith(DEFAULT_SWITCH_PORT_PREFIX):
        return port_label[len(DEFAULT_SWITCH_PORT_PREFIX) :]
    return port_label
