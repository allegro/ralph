import re

from ralph.data_center.models import DataCenter, DataCenterAsset, Rack
from ralph.switchports.models import RackConfiguration


def configure_rack(
    rack: Rack,
    eth1: DataCenterAsset | str,
    eth2: DataCenterAsset | str,
    mgmt: DataCenterAsset | str,
    description: str = "",
) -> RackConfiguration:
    """
    Configures a rack with the provided switch information. If a RackConfiguration already exists for the given rack, it will be updated with the new information.
    Switch can be provided either as a DataCenterAsset instance or "rack{rack_number}u{rack_position}" string (data center inferred from the rack)
    Args:
        rack (Rack): The rack to be configured.
        eth1 (DataCenterAsset): The default switch for eth1 server ports.
        eth2 (DataCenterAsset): The default switch for eth2 server ports.
        mgmt (DataCenterAsset): The default switch for management server ports.
        description (str, optional): A description for the rack configuration. Defaults to an empty string.

    Returns:
        RackConfiguration: The created or updated RackConfiguration instance.
    """
    dc: DataCenter = rack.server_room.data_center
    eth1_switch = _parse(eth1, dc)
    eth2_switch = _parse(eth2, dc)
    mgmt_switch = _parse(mgmt, dc)

    rack_config, created = RackConfiguration.objects.update_or_create(
        rack=rack,
        defaults={
            "eth1_default_switch": eth1_switch,
            "eth2_default_switch": eth2_switch,
            "mgmt_default_switch": mgmt_switch,
            "description": description,
        },
    )
    return rack_config


def _parse(asset: DataCenterAsset | str, dc: DataCenter) -> DataCenterAsset:
    match asset:
        case DataCenterAsset():
            return asset
        case str(position_str):
            match_ = re.match(
                r"rack(?P<rack_number>\d+)u(?P<position>\d+)", position_str
            )
            if not match_:
                raise ValueError(f"Invalid position string: {position_str}")
            try:
                rack = Rack.objects.get(
                    server_room__data_center=dc,
                    name__endswith=match_.group("rack_number"),
                )
                switch = DataCenterAsset.objects.get(
                    rack=rack, position=match_.group("position")
                )
                return switch
            except:  # noqa
                raise ValueError(
                    f"No switch found at position {position_str} in data center {dc.name}"
                )
        case _:
            raise ValueError(f"Invalid asset identifier: {asset}")
