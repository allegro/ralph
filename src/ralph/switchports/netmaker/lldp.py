"""LLDP parsing: turn a raw netmaker ``InterfaceDTO`` into candidate identifiers.

This is the *parsing* half of remote-asset resolution and is where all the
"does this LLDP field actually look like a hostname / MAC" edge cases live.
The DB lookups that turn these strings into assets live in
``asset_matching``.
"""

from django.core.exceptions import ValidationError
from pydantic import BaseModel

from ralph.assets.models.components import mac_validator
from ralph.switchports.netmaker.dto import InterfaceDTO


class RemoteAsset(BaseModel):
    remote_hostname_from_remote_name: str | None
    remote_hostname_from_desc: str | None
    remote_mac_from_remote_id: str | None
    remote_interface_name_from_remote_port: str | None

    @classmethod
    def from_interface_dto(cls, interface: InterfaceDTO) -> "RemoteAsset":
        return cls(
            remote_hostname_from_remote_name=_get_from_remote_hostname_from_remote_name(
                interface
            ),
            remote_hostname_from_desc=_get_remote_hostname_from_desc(interface),
            remote_mac_from_remote_id=_get_remote_mac(interface),
            remote_interface_name_from_remote_port=_get_remote_interface_name(
                interface
            ),
        )


def _get_remote_mac(interface: InterfaceDTO) -> str | None:
    try:
        mac_validator(interface.remote_id)
        return interface.remote_id
    except (ValueError, ValidationError):
        return None


def _get_remote_interface_name(interface: InterfaceDTO) -> str | None:
    return interface.remote_port


def _get_from_remote_hostname_from_remote_name(interface: InterfaceDTO) -> str | None:
    if len(interface.remote_name.split(" ")) > 1:
        return None
    if len(interface.remote_name.split(".")) < 2:
        return None
    return interface.remote_name


def _get_remote_hostname_from_desc(interface: InterfaceDTO) -> str | None:
    desc = interface.desc
    if len(desc.split()) >= 3 and len(desc.split()[0].split(".")) >= 2:
        return desc.split()[0]
    else:
        return None
