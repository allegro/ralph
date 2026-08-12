"""Resolve a user-entered switch identifier to a ``DataCenterAsset``.

Accepts a barcode, a hostname, or a ``rack{n}u{pos}`` position string.
"""

import re

from ralph.data_center.models import DataCenter, DataCenterAsset, Rack

_POSITION_RE = re.compile(r"rack(?P<rack_number>\d+)u(?P<position>\d+)")


def rack_data_center(rack) -> DataCenter | None:
    """Best-effort data center for a rack (may be None if not placed)."""
    server_room = getattr(rack, "server_room", None)
    return getattr(server_room, "data_center", None)


def resolve_switch(identifier: str, dc: DataCenter | None = None) -> DataCenterAsset | None:
    """Resolve a switch from a barcode, hostname or ``rackNuM`` position.

    Resolution order (first match wins):

    1. barcode
    2. hostname
    3. ``rack{n}u{pos}`` position within ``dc`` — only attempted when a data
       center context is available.

    Returns ``None`` when nothing matches (blank input included).
    """
    identifier = (identifier or "").strip()
    if not identifier:
        return None
    for lookup in ({"barcode": identifier}, {"hostname": identifier}):
        try:
            return DataCenterAsset.objects.get(**lookup)
        except DataCenterAsset.DoesNotExist:
            continue
    if dc is not None:
        return resolve_switch_by_position(identifier, dc)
    return None


def resolve_switch_by_position(position_str: str, dc: DataCenter) -> DataCenterAsset | None:
    """Resolve ``rack{n}u{pos}`` to the asset at that rack position in ``dc``.

    ``rack12u42`` is the asset at position 42 of the rack whose name ends with
    ``12``. Returns ``None`` when the string is malformed or no such asset
    exists.
    """
    match = _POSITION_RE.match(position_str.strip())
    if not match:
        return None
    try:
        rack = Rack.objects.get(
            server_room__data_center=dc,
            name__endswith=match.group("rack_number"),
        )
        return DataCenterAsset.objects.get(rack=rack, position=match.group("position"))
    except (
        Rack.DoesNotExist,
        Rack.MultipleObjectsReturned,
        DataCenterAsset.DoesNotExist,
        DataCenterAsset.MultipleObjectsReturned,
    ):
        return None
