"""Config flow for Whoop integration."""
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import WhoopApiClient, WhoopAuthError, WhoopConnectionError
from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET

class WhoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whoop."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                client = WhoopApiClient(
                    async_get_clientsession(self.hass),
                    user_input[CONF_ACCESS_TOKEN],
                )

                # Validate the token
                if await client.validate_token():
                    return self.async_create_entry(
                        title="Whoop",
                        data={
                            CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"

            except WhoopAuthError:
                errors["base"] = "invalid_auth"
            except WhoopConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization."""
        return await self.async_step_user()