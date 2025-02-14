"""Config flow for Whoop integration."""
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import WhoopApiClient, WhoopAuthError, WhoopConnectionError
from .const import DOMAIN, OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL

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
                session = async_get_clientsession(self.hass)
                client = WhoopApiClient(
                    session,
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                )

                # Get OAuth token
                token = await client.get_access_token()
                
                if token:
                    return self.async_create_entry(
                        title="Whoop",
                        data={
                            CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                            CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                            "token": token,
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
                    vol.Required(CONF_CLIENT_ID): cv.string,
                    vol.Required(CONF_CLIENT_SECRET): cv.string,
                }
            ),
            errors=errors,
        )