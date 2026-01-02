import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class AdjustableBedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for BLE Adjustable Bed."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    "address": user_input["address"],
                    "name": user_input["name"],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Adjustable Bed"): str,
                    vol.Required("address"): str,
                }
            ),
        )
