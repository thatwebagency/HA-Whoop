"""API client for Whoop."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

import aiohttp
import async_timeout

from .const import (
    API_BASE_URL,
    DEFAULT_TIMEOUT,
    ENDPOINT_RECOVERY,
    ENDPOINT_SLEEP,
    ENDPOINT_CYCLE,
    ENDPOINT_USER,
    ERROR_AUTH,
    ERROR_CONNECTION,
    ERROR_EXPIRED_TOKEN,
    OAUTH_TOKEN_URL,
    TOKEN_EXPIRY_BUFFER,
)

_LOGGER = logging.getLogger(__name__)

class WhoopApiClient:
    """API client for Whoop."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        session: aiohttp.ClientSession,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expiry: Optional[datetime] = None,
    ) -> None:
        """Initialize the API client."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry = token_expiry
        self._headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}

    async def get_token_from_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": redirect_uri,
        }

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                response = await self._session.post(
                    OAUTH_TOKEN_URL,
                    data=data,
                )
                
                if response.status == 401:
                    raise WhoopAuthError(ERROR_AUTH)
                
                response.raise_for_status()
                token_data = await response.json()
                
                self._access_token = token_data["access_token"]
                self._refresh_token = token_data["refresh_token"]
                self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
                self._headers["Authorization"] = f"Bearer {self._access_token}"
                
                # Verify the token works
                await self.get_user()
                
                return token_data

        except aiohttp.ClientError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err
        except asyncio.TimeoutError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err

    async def refresh_access_token(self) -> dict:
        """Refresh the access token."""
        if not self._refresh_token:
            raise WhoopAuthError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                response = await self._session.post(
                    OAUTH_TOKEN_URL,
                    data=data,
                )
                
                if response.status == 401:
                    raise WhoopAuthError(ERROR_AUTH)
                
                response.raise_for_status()
                token_data = await response.json()
                
                self._access_token = token_data["access_token"]
                self._refresh_token = token_data.get("refresh_token", self._refresh_token)
                self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
                self._headers["Authorization"] = f"Bearer {self._access_token}"
                
                return token_data

        except aiohttp.ClientError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err
        except asyncio.TimeoutError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err

    async def _async_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Any:
        """Make an API request."""
        if self._token_expiry and datetime.now() + timedelta(seconds=TOKEN_EXPIRY_BUFFER) >= self._token_expiry:
            await self.refresh_access_token()

        url = f"{API_BASE_URL}{endpoint}"

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                response = await self._session.request(
                    method,
                    url,
                    headers=self._headers,
                    params=params,
                )
                
                if response.status == 401:
                    if self._refresh_token:
                        await self.refresh_access_token()
                        # Retry the request with new token
                        response = await self._session.request(
                            method,
                            url,
                            headers=self._headers,
                            params=params,
                        )
                    else:
                        raise WhoopAuthError(ERROR_EXPIRED_TOKEN)
                
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err
        except asyncio.TimeoutError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err

    async def get_recovery(self) -> Dict:
        """Get recovery data."""
        return await self._async_request("GET", ENDPOINT_RECOVERY)

    async def get_sleep(self) -> Dict:
        """Get sleep data."""
        return await self._async_request("GET", ENDPOINT_SLEEP)

    async def get_cycle(self) -> Dict:
        """Get cycle data."""
        return await self._async_request("GET", ENDPOINT_CYCLE)

    async def get_user(self) -> Dict:
        """Get user data."""
        return await self._async_request("GET", ENDPOINT_USER)

    async def validate_token(self) -> bool:
        """Validate the access token."""
        try:
            await self.get_user()
            return True
        except (WhoopAuthError, WhoopConnectionError):
            return False


class WhoopError(Exception):
    """Base exception for Whoop."""


class WhoopAuthError(WhoopError):
    """Authentication error."""


class WhoopConnectionError(WhoopError):
    """Connection error."""


class WhoopSubscriptionError(WhoopError):
    """Subscription error."""