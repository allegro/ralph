"""Netmaker integration: HTTP client, wire DTOs and LLDP asset matching.

Public surface is re-exported so call sites can simply do
``from ralph.switchports.netmaker import NetmakerSwitchportBackend, SwitchDTO``.
"""

from ralph.switchports.netmaker.asset_matching import (
    MaybeDCA,
    cross_validate,
    extract_asset,
)
from ralph.switchports.netmaker.backend import (
    NetmakerSwitchportBackend,
    SwitchportSyncBackend,
)
from ralph.switchports.netmaker.dto import (
    InterfaceDTO,
    InterfaceMode,
    InterfaceStatus,
    RefreshStatus,
    SwitchDTO,
    Vlan,
)
from ralph.switchports.netmaker.lldp import RemoteAsset

__all__ = [
    "InterfaceDTO",
    "InterfaceMode",
    "InterfaceStatus",
    "MaybeDCA",
    "NetmakerSwitchportBackend",
    "RefreshStatus",
    "RemoteAsset",
    "SwitchDTO",
    "SwitchportSyncBackend",
    "Vlan",
    "cross_validate",
    "extract_asset",
]
