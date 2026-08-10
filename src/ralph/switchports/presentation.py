"""Presentation helpers for rendering netmaker backend validation results.

Shared between the rack switchport grid and the DataCenterAsset "Ports" tab so
that both render the netmaker cell (asset match, link/admin state, speed and the
expandable raw JSON) in exactly the same way.
"""

import json


from ralph.switchports.models import ValidationStatus, BackendValidationResult


def format_speed(speed):
    """Format an interface speed in Mbps into a compact human-readable string."""
    if not speed:
        return ""
    if speed >= 1000:
        value = speed / 1000
        if value == int(value):
            return f"{int(value)}G"
        return f"{value:.1f}G"
    return f"{speed}M"


def status_symbol(status):
    """Map a backend status string to a shape-encoded glyph (not color-reliant)."""
    return {
        "up": "\u2191",  # up arrow
        "down": "\u2193",  # down arrow
    }.get((status or "").lower(), "?")


def _attach_port_metrics(data: dict, vr: BackendValidationResult):
    """Attach the shared link/admin/speed badges and raw JSON to a cell dict."""
    data["status"] = vr.status
    data["oper_status"] = vr.oper_status
    data["admin_status"] = vr.admin_status
    data["oper_symbol"] = status_symbol(vr.oper_status)
    data["admin_symbol"] = status_symbol(vr.admin_status)
    data["speed"] = vr.speed
    data["speed_display"] = format_speed(vr.speed)
    data["remote_id"] = vr.raw_data.get("remote_id")
    data["desc"] = vr.raw_data.get("desc")
    if vr.raw_data:
        data["raw_json"] = json.dumps(vr.raw_data, indent=2, ensure_ascii=False, sort_keys=True)
    return data


def build_validation_context(vr: BackendValidationResult, expected_asset_id=None) -> dict:
    """Build the template context dict for a single BackendValidationResult.

    ``expected_asset_id`` is the id of the asset we expect netmaker to report on
    the other side of the port; it is used to mark a match (green) vs mismatch
    (orange). Returns ``None`` when there is nothing to render.
    """
    if vr is None:
        return None

    if vr.status == ValidationStatus.ASSET_FOUND:
        match = (
            vr.remote_asset_id == expected_asset_id
            if vr.remote_asset_id and expected_asset_id is not None
            else False
        )
        data = {
            "css_class": "validation-ok" if match else "validation-mismatch",
            "label": vr.remote_asset.hostname if vr.remote_asset else vr.remote_hostname,
            "remote_asset": vr.remote_asset,
            "match": match,
        }
    elif vr.status == ValidationStatus.ASSET_CONFLICT:
        data = {
            "css_class": "validation-error",
            "label": (f"CONFLICT ({vr.remote_hostname})" if vr.remote_hostname else "CONFLICT"),
            "remote_asset": vr.remote_asset,
        }
    elif vr.status == ValidationStatus.PORT_NOT_FOUND:
        data = {"css_class": "validation-warning", "label": "empty"}
    elif vr.status == ValidationStatus.SWITCH_NOT_FOUND:
        data = {"css_class": "validation-error", "label": "SWITCH N/F"}
    else:
        return None

    return _attach_port_metrics(data, vr)
