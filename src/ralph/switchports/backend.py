from __future__ import annotations

import logging
from enum import Enum
from typing import Any
from urllib.error import HTTPError

import requests
from django.conf import settings
from pydantic import BaseModel, Field, ConfigDict

from ralph.data_center.models import DataCenterAsset

logger = logging.getLogger(__name__)


class InterfaceStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKOWN = "unknown"
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


class Interface(BaseModel):
    name: str = Field(..., description="Interface short name, e.g. '0/0/0'")
    name_cfg: str = Field(..., description="Interface config name, e.g. 'xe-0/0/0'")
    speed: int = Field(..., description="Interface speed in Mbps")
    desc: str = Field("", description="Interface description")
    uplink: bool = Field(False, description="Whether this is an uplink interface")
    status: InterfaceStatus = Field(..., description="Operational status")
    admin_status: InterfaceStatus = Field(..., description="Administrative status")
    interface_mode: InterfaceMode = Field(
        ..., description="Interface mode (access/trunk)"
    )
    remote_name: str | None = Field(None, description="LLDP remote system name")
    remote_id: str | None = Field(None, description="LLDP remote chassis ID (MAC)")
    remote_port: str | None = Field(None, description="LLDP remote port identifier")
    vlans: list[Vlan] = Field(
        default_factory=list, description="List of assigned VLANs"
    )
    native_vlan: int | None = Field(None, description="Native VLAN ID")
    mtu: str = Field(..., description="Maximum transmission unit")


class SwitchOutput(BaseModel):
    hostname: str = Field(..., description="Switch hostname")
    ralph_id: str = Field(..., description="Ralph ID of the switch")
    ports: list[Interface] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class JobId(str):
    pass


class SwitchportSyncBackend:
    def get_switchports(self, switch: DataCenterAsset) -> SwitchOutput:
        raise NotImplementedError

    def trigger_switch_refresh_on_backend(self, switch: DataCenterAsset) -> JobId:
        raise NotImplementedError

    def refresh_status(self, job_id: JobId) -> RefreshStatus:
        raise NotImplementedError


class NetmakerSwitchportBackend(SwitchportSyncBackend):
    def __init__(self):
        self.host = settings.NETMAKER_HOST

    def _switches_url(self):
        return f"{self.host}/api/switchApp/switch"

    def _switchports_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}"

    def _auth(self) -> dict:
        oauth_token = settings.JWT_TOKEN
        return {"Authorization": f"Bearer {oauth_token}"}

    def get_switches(self) -> list[str]:
        response = requests.get(self._switches_url(), headers=self._auth())
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return response["hostnames"]

    def get_switchports(self, switch: DataCenterAsset) -> SwitchOutput:
        response = requests.get(
            self._switchports_url(switch.hostname), headers=self._auth()
        )
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return SwitchOutput(**response["result"])

    def trigger_switch_refresh_on_backend(self, switch: DataCenterAsset) -> JobId:
        pass


if True:
    # Example usage
    backend = NetmakerSwitchportBackend()
    switch = DataCenterAsset(hostname="rack105-sw1.dc4.local")
    try:
        switchports = backend.get_switchports(switch)
        print(switchports)
    except HTTPError as e:
        print(f"Failed to get switchports: {e}")
