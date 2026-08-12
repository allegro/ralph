from __future__ import annotations

import logging
import os
from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


from ralph.data_center.models import DataCenterAsset
from ralph.switchports.netmaker.dto import SwitchDTO, RefreshStatus

logger = logging.getLogger(__name__)


class JobId(str):
    pass


class OauthTokenAuthMixin:
    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def _get_token(self):
        if token := os.environ.get("OAUTH_TOKEN"):
            return token
        raise ImproperlyConfigured("OAUTH_TOKEN env is not set")


class StaticTokenMixin:
    def _auth(self) -> dict:
        return {"Authorization": f"Token {self._get_token()}"}

    def _get_token(self) -> str:
        if token := settings.NETMAKER_TOKEN:
            return token
        raise ImproperlyConfigured("NETMAKER_TOKEN env is not set")


class SwitchportSyncBackend:
    def get_switchports(self, switch: DataCenterAsset) -> SwitchDTO:
        raise NotImplementedError

    def refresh_status(self, job_id: JobId) -> RefreshStatus:
        raise NotImplementedError


class NetmakerSwitchportBackendBase(SwitchportSyncBackend):
    def __init__(self, *args, **kwargs):
        self.host = settings.NETMAKER_HOST
        super().__init__(*args, **kwargs)

    def _switches_url(self):
        return f"{self.host}/api/switchApp/switch"

    def _switchports_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}"

    def _switch_refresh_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}/refresh"

    def get_switches(self) -> list[str]:
        response = requests.get(self._switches_url(), headers=self._auth())
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return response["hostnames"]

    def get_switchports(self, switch_hostname: str) -> SwitchDTO:
        response = requests.get(self._switchports_url(switch_hostname), headers=self._auth())
        response.raise_for_status()
        response: dict[str, Any] = response.json()
        if not response.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response.get('status')}", response=response
            )

        return SwitchDTO(**response["result"])

    def refresh_switch(self, switch_hostname: str) -> dict:
        """Trigger a backend (netmaker) refresh of a single switch.

        The switchApp backend performs this refresh synchronously within the
        request, so this call blocks until the switch data has been re-pulled
        from netmaker and stored on the backend side.
        """
        response = requests.post(self._switch_refresh_url(switch_hostname), headers=self._auth())
        response.raise_for_status()
        response_dict: dict[str, Any] = response.json()
        if not response_dict.get("success"):
            raise requests.exceptions.HTTPError(
                f"Response with status {response_dict.get('status')}", response=response
            )

        return response_dict


class NetmakerSwitchportBackend(NetmakerSwitchportBackendBase, StaticTokenMixin):
    pass


class NetmakerSwitchportBackendOauth(NetmakerSwitchportBackendBase, OauthTokenAuthMixin):
    pass
