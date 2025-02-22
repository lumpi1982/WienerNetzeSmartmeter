from copy import deepcopy
import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .api import Smartmeter
from .const import ATTRS_ZAEHLPUNKTE_CALL, DOMAIN, CONF_ZAEHLPUNKTE
from .utils import translate_dict

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
     vol.Required(CONF_USERNAME): cv.string,
     vol.Required(CONF_PASSWORD): cv.string
    }
)

class WienerNetzeSmartMeterCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wiener Netze Smartmeter config flow"""

    data: Optional[Dict[str, Any]]

    async def validate_auth(self, username: str, password: str) -> list[dict]:
        """
        Validates credentials for smartmeter.
        Raises a ValueError if the auth credentials are invalid.
        """
        api = Smartmeter(username, password)
        await self.hass.async_add_executor_job(api.login)
        zps = await self.hass.async_add_executor_job(api.zaehlpunkte)
        return zps[0]["zaehlpunkte"] if zps is not None else []

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                zps = await self.validate_auth(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            except Exception as e:
                _LOGGER.error("Error validating Wiener Netze auth")
                _LOGGER.exception(e)
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data
                self.data = user_input
                self.data[CONF_ZAEHLPUNKTE] = [translate_dict(zp, ATTRS_ZAEHLPUNKTE_CALL) for zp in zps]
                # User is done authenticating, create entry
                return self.async_create_entry(title="Wiener Netze Smartmeter", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )
