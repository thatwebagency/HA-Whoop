"""Config flow for Whoop integration."""
from typing import Any
import secrets
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import WhoopApiClient, WhoopAuthError, WhoopConnectionError
from .const import (
    DOMAIN,
    OAUTH_AUTHORIZE_URL,
    OAUTH_TOKEN_URL,
    AUTH_CALLBACK_PATH,
    AUTH_CALLBACK_NAME,
)

class WhoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whoop."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._state: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]
            self._state = secrets.token_urlsafe(16)

            # Register callback
            self.hass.http.register_view(WhoopAuthCallbackView())

            # Generate authorization URL
            authorize_url = (
                f"{OAUTH_AUTHORIZE_URL}"
                f"?client_id={self._client_id}"
                f"&redirect_uri={self.hass.config.api.base_url}{AUTH_CALLBACK_PATH}"
                f"&response_type=code"
                f"&state={self._state}"
                f"&scope=offline read:recovery read:sleep read:workout"
            )

            return self.async_external_step(
                step_id="auth",
                url=authorize_url,
            )

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

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the auth callback."""
        return self.async_external_step_done(next_step_id="finish")

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle completion of the OAuth flow."""
        if not self.context.get("code"):
            return self.async_abort(reason="no_code")

        client = WhoopApiClient(
            async_get_clientsession(self.hass),
            client_id=self._client_id,
            client_secret=self._client_secret,
        )

        try:
            token = await client.get_token_from_code(
                self.context["code"],
                f"{self.hass.config.api.base_url}{AUTH_CALLBACK_PATH}",
            )

            return self.async_create_entry(
                title="Whoop",
                data={
                    CONF_CLIENT_ID: self._client_id,
                    CONF_CLIENT_SECRET: self._client_secret,
                    "token": token,
                },
            )
        except WhoopAuthError:
            return self.async_abort(reason="invalid_auth")
        except WhoopConnectionError:
            return self.async_abort(reason="cannot_connect")


class WhoopAuthCallbackView:
    """Whoop Authorization Callback View."""

    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME
    requires_auth = False

    async def get(self, request):
        """Handle authorization callback."""
        hass = request.app["hass"]
        state = request.query.get("state")
        code = request.query.get("code")

        for flow in hass.config_entries.flow.async_progress():
            if (
                flow["handler"] == DOMAIN
                and flow["context"].get("state") == state
            ):
                hass.config_entries.flow.async_configure(
                    flow["flow_id"],
                    {"code": code},
                )
                return aiohttp.web.Response(
                    text="Authorization completed. You can close this window."
                )

        return aiohttp.web.Response(status=400)