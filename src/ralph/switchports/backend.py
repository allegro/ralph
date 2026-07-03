from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

from ralph.data_center.models import DataCenterAsset
from ralph.lib.cache.file_cache import file_cache
from ralph.switchports.dto import SwitchDTO, RefreshStatus

logger = logging.getLogger(__name__)


class JobId(str):
    pass


class SwitchportSyncBackend:
    def get_switchports(self, switch: DataCenterAsset) -> SwitchDTO:
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

    def _switch_refresh_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}/refresh"

    def _auth(self) -> dict:
        oauth_token = settings.JWT_TOKEN
        return {"Authorization": f"Bearer {oauth_token}"}

    @file_cache("get_switches")
    def get_switches(self) -> list[str]:
        response = requests.get(self._switches_url(), headers=self._auth())
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return response["hostnames"]

    @file_cache("get_switchports")
    def get_switchports(self, switch_hostname: str) -> SwitchDTO:
        response = requests.get(
            self._switchports_url(switch_hostname), headers=self._auth()
        )
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return SwitchDTO(**response["result"])

    def refresh_switch(self, switch_hostname: str) -> dict:
        response = requests.post(
            self._switch_refresh_url(switch_hostname), headers=self._auth()
        )
        response.raise_for_status()
        response_dict: dict[str, Any] = response.json()
        if not response_dict.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response_dict.get('status')}", response=response
            )

        return response_dict
