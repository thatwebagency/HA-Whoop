"""The Whoop integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhoopApiClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Whoop from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    client = WhoopApiClient(
        async_get_clientsession(hass),
        entry.data["token"]
    )

    coordinator = WhoopDataUpdateCoordinator(
        hass,
        client=client,
    )

    await coordinator.async_config_entry_first_refresh()

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
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.client = client
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                # Get all required data from API
                recovery = await self.client.get_recovery()
                sleep = await self.client.get_sleep()
                cycle = await self.client.get_cycle()
                
                return {
                    "recovery": recovery,
                    "sleep": sleep,
                    "cycle": cycle
                }
        except Exception as error:
            raise UpdateFailed(error) from error