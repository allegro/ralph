from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class InterfaceStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    OTHER = "other"


class InterfaceMode(str, Enum):
    ACCESS = "access"
    TRUNK = "trunk"


class RefreshStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    IN_PROGRESS = "in_progress"
    UNKNOWN = "unknown"


class Vlan(BaseModel):
    vlan_id: int
    name: str


class InterfaceDTO(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Interface short name, e.g. '0/0/0'")
    name_cfg: str = Field(..., description="Interface config name, e.g. 'xe-0/0/0'")
    speed: int | None = Field(..., description="Interface speed in Mbps")
    desc: str = Field("", description="Interface description")
    uplink: bool = Field(False, description="Whether this is an uplink interface")
    status: InterfaceStatus = Field(..., description="Operational status")
    admin_status: InterfaceStatus = Field(..., description="Administrative status")
    interface_mode: InterfaceMode = Field(..., description="Interface mode (access/trunk)")
    remote_name: str = Field(..., description="LLDP remote system name")
    remote_id: str | None = Field(None, description="LLDP remote chassis ID (MAC)")
    remote_port: str | None = Field(None, description="LLDP remote port identifier")
    vlans: list[Vlan] = Field(default_factory=list, description="List of assigned VLANs")
    native_vlan: Vlan | None = Field(None, description="Native VLAN ID")
    mtu: str = Field(..., description="Maximum transmission unit")


class SwitchDTO(BaseModel):
    hostname: str = Field(..., description="Switch hostname")
    sn: str = Field(..., description="Switch serial number")
    barcode: str = Field(..., description="Switch barcode")
    model: str = Field(..., description="Switch model")
    ansible_unify_model: str = Field(..., description="Ansible unify model name")
    acs_device_type: str = Field(..., description="ACS device type")
    ralph_id: int = Field(..., description="Ralph ID of the switch")
    ports: list[InterfaceDTO] = Field(default_factory=list)
    location_rack: str = Field(..., description="Rack location")
    location_dc: str = Field(..., description="Data center location")
    location_position: int = Field(..., description="Position in rack", strict=False)
    model_config = ConfigDict(extra="allow")

    @property
    def manufacturer_name(self) -> str | None:
        return self.acs_device_type.split("#")[-1].title() if self.acs_device_type else None
