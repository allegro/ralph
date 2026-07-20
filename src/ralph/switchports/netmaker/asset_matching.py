"""Resolve LLDP-parsed identifiers to Ralph assets and cross-check them.

The parsing lives in ``lldp``; here we do the DB lookups (hostname, CloudHost
hypervisor fallback, MAC → Ethernet → asset) and the tri-state
``cross_validate`` used to flag ASSET_FOUND / ASSET_CONFLICT / not-found.
"""

from typing import TypeAlias

from ralph.assets.models import Ethernet
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.netmaker.lldp import RemoteAsset
from ralph.virtual.models import CloudHost

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
