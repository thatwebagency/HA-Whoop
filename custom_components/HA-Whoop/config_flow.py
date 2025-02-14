"""Config flow for Whoop integration."""
from typing import Any
import secrets
from datetime import datetime, timedelta
import voluptuous as vol
import aiohttp

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
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    OAUTH_SCOPES,
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
            
            # Check if already configured
            await self.async_set_unique_id(self._client_id)
            self._abort_if_unique_id_configured()

            self._state = secrets.token_urlsafe(16)

            # Register callback
            self.hass.http.register_view(WhoopAuthCallbackView())

            # Generate authorization URL with all required scopes
            scope_string = "%20".join(OAUTH_SCOPES)
            authorize_url = (
                f"{OAUTH_AUTHORIZE_URL}"
                f"?client_id={self._client_id}"
                f"&redirect_uri={self.hass.config.api.base_url}{AUTH_CALLBACK_PATH}"
                f"&response_type=code"
                f"&state={self._state}"
                f"&scope={scope_string}"
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
        if not self.context.get("code"):
            return self.async_abort(reason="missing_code")

        if self.context.get("state") != self._state:
            return self.async_abort(reason="invalid_state")

        return self.async_external_step_done(next_step_id="finish")

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle completion of the OAuth flow."""
        if not self.context.get("code"):
            return self.async_abort(reason="missing_code")

        client = WhoopApiClient(
            client_id=self._client_id,
            client_secret=self._client_secret,
            session=async_get_clientsession(self.hass),
        )

        try:
            token_info = await client.get_token_from_code(
                self.context["code"],
                f"{self.hass.config.api.base_url}{AUTH_CALLBACK_PATH}",
            )

            # Calculate expiry timestamp
            expiry_timestamp = int((datetime.now() + timedelta(seconds=token_info["expires_in"])).timestamp())

            return self.async_create_entry(
                title="Whoop",
                data={
                    CONF_CLIENT_ID: self._client_id,
                    CONF_CLIENT_SECRET: self._client_secret,
                    CONF_ACCESS_TOKEN: token_info["access_token"],
                    CONF_REFRESH_TOKEN: token_info["refresh_token"],
                    CONF_TOKEN_EXPIRY: expiry_timestamp,
                },
            )
        except WhoopAuthError:
            return self.async_abort(reason="invalid_auth")
        except WhoopConnectionError:
            return self.async_abort(reason="cannot_connect")

    async def async_step_reauth(self, user_input=None):
        """Handle reauthorization."""
        return await self.async_step_user()


class WhoopAuthCallbackView(aiohttp.web.View):
    """Whoop Authorization Callback View."""

    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME
    requires_auth = False

    async def get(self) -> aiohttp.web.Response:
        """Handle authorization callback."""
        hass = self.request.app["hass"]
        code = self.request.query.get("code")
        state = self.request.query.get("state")

        if not code:
            return aiohttp.web.Response(status=400, text="No code provided")

        for flow in hass.config_entries.flow.async_progress():
            if (
                flow["handler"] == DOMAIN
                and flow["context"].get("state") == state
            ):
                await hass.config_entries.flow.async_configure(
                    flow["flow_id"],
                    {"code": code},
                )
                return aiohttp.web.Response(
                    text="<html><body>Authorization completed! You can close this window.</body></html>",
                    content_type="text/html",
                )

        return aiohttp.web.Response(status=400, text="Invalid state")