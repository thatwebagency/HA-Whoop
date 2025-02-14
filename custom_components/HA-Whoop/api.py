"""API client for Whoop."""
from typing import Any, Dict, Optional
import aiohttp
import async_timeout
import logging

from .const import (
    API_BASE_URL,
    DEFAULT_TIMEOUT,
    ENDPOINT_RECOVERY,
    ENDPOINT_SLEEP,
    ENDPOINT_CYCLE,
    ENDPOINT_USER,
    ERROR_AUTH,
    ERROR_CONNECTION,
)

_LOGGER = logging.getLogger(__name__)

class WhoopApiClient:
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
                
                # Verify the token works by making a test API call
                self._access_token = token_data["access_token"]
                self._headers["Authorization"] = f"Bearer {self._access_token}"
                
                # Test API access
                await self.get_user()
                
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
                    raise WhoopAuthError(ERROR_AUTH)
                elif response.status == 404 and "Subscription not found" in await response.text():
                    raise WhoopSubscriptionError("Active Whoop subscription required")
                
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err
        except asyncio.TimeoutError as err:
            raise WhoopConnectionError(ERROR_CONNECTION) from err
            
    async def get_access_token(self) -> str:
        """Get OAuth access token."""
        data = {
            "grant_type": "client_credentials",
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
                result = await response.json()
                
                self._access_token = result.get("access_token")
                self._headers["Authorization"] = f"Bearer {self._access_token}"
                
                return self._access_token

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
                    raise WhoopAuthError(ERROR_AUTH)
                
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