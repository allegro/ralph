"""Shared test helpers for building netmaker DTOs."""

from ralph.switchports.netmaker.dto import (
    InterfaceDTO,
    InterfaceMode,
    InterfaceStatus,
    SwitchDTO,
)


def make_interface(
    name, remote_name="", remote_id=None, remote_port=None, desc=""
) -> InterfaceDTO:
    """Build an InterfaceDTO with sensible defaults for tests."""
    return InterfaceDTO(
        name=name,
        name_cfg=f"xe-{name}",
        speed=10000,
        desc=desc,
        uplink=False,
        status=InterfaceStatus.UP,
        admin_status=InterfaceStatus.UP,
        interface_mode=InterfaceMode.ACCESS,
        remote_name=remote_name,
        remote_id=remote_id,
        remote_port=remote_port,
        mtu="9216",
    )


def make_switch_dto(ralph_id, ports, hostname="sw1.dc.example.com") -> SwitchDTO:
    """Build a SwitchDTO wrapping the given ports."""
    return SwitchDTO(
        hostname=hostname,
        sn="SN123",
        barcode="BC123",
        model="TestModel",
        ansible_unify_model="test",
        acs_device_type="vendor#TestVendor",
        ralph_id=ralph_id,
        location_rack="TestRack",
        location_dc="DC1",
        location_position=44,
        ports=ports,
    )
