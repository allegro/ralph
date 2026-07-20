from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests
from django.conf import settings

from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import CustomOAuth2Error
from requests_oauthlib import OAuth2Session

from ralph.data_center.models import DataCenterAsset
from ralph.switchports.netmaker.dto import SwitchDTO, RefreshStatus

logger = logging.getLogger(__name__)


class JobId(str):
    pass


class OauthTokenAuthMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token_expiration = None
        self._token = None

    def _get_token(self):
        if self._token_expiration is None or datetime.now() > self._token_expiration or self._token is None:
            return self._fetch_oauth_token()
        else:
            return self._token

    def _fetch_oauth_token(self):
        client_id = settings.OAUTH_CLIENT_ID
        secret = settings.OAUTH_SECRET
        token_url = settings.OAUTH_TOKEN_URL
        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        try:
            token = oauth.fetch_token(
                token_url=token_url, client_id=client_id, client_secret=secret
            )
        except CustomOAuth2Error as e:
            logger.error(str(e))
            return None

        expire_in = token.get("expires_in")
        self._token_expiration = datetime.now() + timedelta(0, expire_in - 60)
        self._token = token.get("access_token")
        return self._token


class SwitchportSyncBackend:
    def get_switchports(self, switch: DataCenterAsset) -> SwitchDTO:
        raise NotImplementedError

    def refresh_status(self, job_id: JobId) -> RefreshStatus:
        raise NotImplementedError


class NetmakerSwitchportBackend(SwitchportSyncBackend, OauthTokenAuthMixin):
    def __init__(self, *args, **kwargs):
        self.host = settings.NETMAKER_HOST
        super().__init__(*args, **kwargs)

    def _switches_url(self):
        return f"{self.host}/api/switchApp/switch"

    def _switchports_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}"

    def _switch_refresh_url(self, hostname: str) -> str:
        return f"{self.host}/api/switchApp/switch/{hostname}/refresh"

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

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
        """Trigger a backend (netmaker) refresh of a single switch.

        The switchApp backend performs this refresh synchronously within the
        request, so this call blocks until the switch data has been re-pulled
        from netmaker and stored on the backend side.
        """
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
