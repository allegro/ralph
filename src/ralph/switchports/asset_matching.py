from typing import TypeAlias

from django.core.exceptions import ValidationError
from pydantic import BaseModel

from ralph.assets.models import Ethernet
from ralph.assets.models.components import mac_validator
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.dto import InterfaceDTO
from ralph.virtual.models import CloudHost


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


MaybeDCA: TypeAlias = DataCenterAsset | None


def extract_asset(remote_asset: RemoteAsset) -> tuple[MaybeDCA, MaybeDCA, MaybeDCA]:
    """
    Try to extract a DataCenterAsset from the given RemoteAsset using the following methods in order:
    1. Match remote_hostname_from_remote_name to a DataCenterAsset hostname
    2. Match remote_hostname_from_desc to a DataCenterAsset hostname
    3. Match remote_mac_from_remote_id to an Ethernet MAC address and return the associated DataCenterAsset

    Returns a tuple of (DataCenterAsset or None, DataCenterAsset or None, DataCenterAsset or None) where each element corresponds to the result of each method.
    """
    asset_from_remote_name: MaybeDCA = None
    asset_from_desc: MaybeDCA = None
    asset_from_mac: MaybeDCA = None

    # remote_name
    if remote_asset.remote_hostname_from_remote_name:
        try:
            asset_from_remote_name = DataCenterAsset.objects.get(
                hostname=remote_asset.remote_hostname_from_remote_name
            )
        except DataCenterAsset.DoesNotExist:
            try:
                cloud_host_from_remote_name = CloudHost.objects.get(
                    hostname=remote_asset.remote_hostname_from_remote_name
                )
                asset_from_remote_name = cloud_host_from_remote_name.hypervisor
            except CloudHost.DoesNotExist:
                pass

    # desc
    if remote_asset.remote_hostname_from_desc:
        try:
            asset_from_desc = DataCenterAsset.objects.get(
                hostname=remote_asset.remote_hostname_from_desc
            )
        except DataCenterAsset.DoesNotExist:
            try:
                cloud_host_from_remote_name = CloudHost.objects.get(
                    hostname=remote_asset.remote_hostname_from_desc
                )
                asset_from_desc = cloud_host_from_remote_name.hypervisor
            except CloudHost.DoesNotExist:
                pass

    # mac
    if remote_asset.remote_mac_from_remote_id:
        try:
            eth = Ethernet.objects.get(mac=remote_asset.remote_mac_from_remote_id)
            asset_from_mac = DataCenterAsset.objects.get(id=eth.base_object.id)
        except (Ethernet.DoesNotExist, DataCenterAsset.DoesNotExist):
            pass

    return asset_from_remote_name, asset_from_desc, asset_from_mac


def next_mac(mac: str) -> str:
    """
    Returns the next MAC address in sequence.
    >>> next_mac('00:1A:2B:3C:4D:5E')
    '00:1A:2B:3C:4D:5F'
    >>> next_mac('FF:FF:FF:FF:FF:FF')
    '00:00:00:00:00:00'
    """
    try:
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        next_mac_bytes = (int.from_bytes(mac_bytes, byteorder="big") + 1) % (1 << 48)
        next_mac_str = ":".join(
            f"{(next_mac_bytes >> (i * 8)) & 0xFF:02X}" for i in reversed(range(6))
        )
        return next_mac_str
    except ValueError:
        raise ValidationError(f"Invalid MAC address format: {mac}")


def previous_mac(mac: str) -> str:
    """
    Returns the previous MAC address in sequence.
    >>> previous_mac('00:1A:2B:3C:4D:5E')
    '00:1A:2B:3C:4D:5D'
    >>> previous_mac('00:00:00:00:00:00')
    'FF:FF:FF:FF:FF:FF'
    """
    try:
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        previous_mac_bytes = (int.from_bytes(mac_bytes, byteorder="big") - 1) % (
            1 << 48
        )
        previous_mac_str = ":".join(
            f"{(previous_mac_bytes >> (i * 8)) & 0xFF:02X}" for i in reversed(range(6))
        )
        return previous_mac_str
    except ValueError:
        raise ValidationError(f"Invalid MAC address format: {mac}")


def cross_validate(*assets: MaybeDCA) -> bool | None:
    """
    Cross validate the given DataCenterAssets by checking if they are all the same non-None asset.
    Returns True if all non-None assets are the same, False if there are conflicting non-None assets, and None if all assets are None.
    """
    non_none_assets = [asset for asset in assets if asset is not None]
    if not non_none_assets:
        return None
    first_asset = non_none_assets[0]
    for asset in non_none_assets[1:]:
        if asset != first_asset:
            return False
    return True


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
