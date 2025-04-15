import re
from typing import Union

from django.utils.translation import gettext_lazy as _

from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus


def assign_management_hostname_and_ip(modeladmin, request, queryset):
    for dca in queryset:
        try:
            if not modeladmin.has_change_permission(request, obj=dca):
                raise RuntimeError("insufficient permissions")
            if not dca.rack.server_room.data_center.management_hostname_suffix:
                raise RuntimeError("dc doesn't have hostname suffix configured")
            if not dca.rack.server_room.data_center.management_ip_prefix:
                raise RuntimeError("dc doesn't have IP prefix configured")
            if dca.status not in {
                DataCenterAssetStatus.used.id,
                DataCenterAssetStatus.to_deploy.id,
            }:
                raise RuntimeError("asset should be in status 'in use' or 'to deploy'")
            try:
                rack_number_int = int(
                    re.match(r".*?(\d+).*?", dca.rack.name).groups()[0]
                )
                rack_number = "%03d" % rack_number_int  # type: str
            except:  # noqa
                raise RuntimeError(f"invalid rack name {dca.rack.name}")

            hostname = _infer_hostname(dca, rack_number)
            if not hostname:
                raise RuntimeError("couldn't infer management hostname")

            if dca.slot_no:  # blade server
                dca.management_hostname = hostname
                modeladmin.message_user(
                    request,
                    f"Updated management hostname for asset id: {dca.id}",
                    level="INFO",
                )
                continue
            else:
                ip = _infer_ip(dca, rack_number)  # others (i.e. server rack)
                if ip:
                    dca.management_ip = ip
                    dca.management_hostname = hostname
                    modeladmin.message_user(
                        request,
                        f"Updated management hostname and IP for asset id: {dca.id}",
                        level="INFO",
                    )
                    continue
            raise RuntimeError("unknown error")
        except Exception as e:  # noqa
            modeladmin.message_user(
                request, f"Can't update asset id: {dca.id}: {e}", level="ERROR"
            )
            return


assign_management_hostname_and_ip.short_description = _(
    "Assign management hostname and IP"
)


def _infer_hostname(asset: DataCenterAsset, rack_number: str) -> Union[str, None]:
    dc = asset.rack.server_room.data_center
    hostname_suffix = dc.management_hostname_suffix
    asset_position = asset.position
    asset_slot = asset.slot_no
    if dc and hostname_suffix and asset_position:
        if asset_slot:
            return f"rack{rack_number}-{asset_position}u-bay{asset_slot}-mgmt.{hostname_suffix}"
        else:
            return f"rack{rack_number}-{asset_position}u-mgmt.{hostname_suffix}"
    else:
        return None


def _infer_ip(asset: DataCenterAsset, rack_number: str) -> Union[str, None]:
    try:
        ip_prefix = asset.rack.server_room.data_center.management_ip_prefix
        # invert the numbers to fit into ip 3rd octet e.g. 503 -> X.X.053.X
        # this should always be ok because of rack naming conventions
        # convert to int to remove zeros at the beginning
        rack_ip_part = int(rack_number[1] + rack_number[0] + rack_number[2])
        assert int(rack_ip_part) <= 255
    except:  # noqa
        raise RuntimeError(f"invalid rack name {asset.rack.name}")

    try:
        position_ip_part = asset.position + 200  # a magic number
        if ip_prefix and rack_ip_part and position_ip_part:
            return f"{ip_prefix}.{rack_ip_part}.{position_ip_part}"
    except:  # noqa
        raise RuntimeError("can't infer management IP address")
