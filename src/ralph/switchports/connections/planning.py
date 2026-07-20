"""Read-only questions about the connection graph used to gate grid edits.

Kept separate from ``strategies`` (which *mutate* the graph) so the view can
ask "who already sits on this switch port?" before deciding whether an edit is a
safe connect or a destructive steal that needs explicit confirmation.
"""

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.models import Port


def switch_port_owner(
    target_switch: DataCenterAsset,
    port_label: str,
    this_asset: DataCenterAsset,
) -> DataCenterAsset | None:
    """Return the asset currently occupying ``target_switch:port_label``.

    Only a *different* asset than ``this_asset`` counts as an owner (a port
    already wired to ``this_asset`` is not a conflict, it is a no-op). Returns
    ``None`` when the switch port does not exist, is unconnected, or is only
    connected to ``this_asset``.
    """
    try:
        switch_port = Port.objects.get(
            label=port_label, data_center_asset=target_switch
        )
    except Port.DoesNotExist:
        return None
    member = getattr(switch_port, "connectionmember", None)
    if member is None:
        return None
    for peer in member.connection.members.select_related(
        "port__data_center_asset"
    ):
        owner = peer.port.data_center_asset
        if owner.id not in (this_asset.id, target_switch.id):
            return owner
    return None
