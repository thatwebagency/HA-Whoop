"""The Whoop integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta, datetime
import logging
from typing import Any

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import WhoopApiClient, WhoopAuthError, WhoopConnectionError
from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Whoop from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    client = WhoopApiClient(
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        session=async_get_clientsession(hass),
        access_token=entry.data[CONF_ACCESS_TOKEN],
        refresh_token=entry.data[CONF_REFRESH_TOKEN],
        token_expiry=datetime.fromtimestamp(entry.data[CONF_TOKEN_EXPIRY])
    )

    coordinator = WhoopDataUpdateCoordinator(
        hass,
        client=client,
        entry=entry,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        # If first refresh fails with auth error, trigger reauth flow
        _LOGGER.error("Authentication failed. Please reauthenticate.")
        raise ConfigEntryAuthFailed

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class WhoopDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Whoop data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WhoopApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.client = client
        self.entry = entry
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                # Validate token before making requests
                if not await self.client.validate_token():
                    try:
                        token_info = await self.client.refresh_access_token()
                        # Update config entry with new tokens
                        new_data = {
                            **self.entry.data,
                            CONF_ACCESS_TOKEN: token_info["access_token"],
                            CONF_REFRESH_TOKEN: token_info.get("refresh_token", self.entry.data[CONF_REFRESH_TOKEN]),
                            CONF_TOKEN_EXPIRY: token_info["expires_in"],
                        }
                        self.hass.config_entries.async_update_entry(
                            self.entry,
                            data=new_data,
                        )
                    except WhoopAuthError as err:
                        raise ConfigEntryAuthFailed from err

                # Get all required data from API
                recovery = await self.client.get_recovery()
                sleep = await self.client.get_sleep()
                cycle = await self.client.get_cycle()
                
                return {
                    "recovery": recovery,
                    "sleep": sleep,
                    "cycle": cycle
                }
        except WhoopAuthError as err:
            raise ConfigEntryAuthFailed from err
        except WhoopConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err