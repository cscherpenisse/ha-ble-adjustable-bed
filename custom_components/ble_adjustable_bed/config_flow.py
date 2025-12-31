import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


class IPixelBklightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for BK-Light iPixel."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    "address",
                    description={"suggested_value": "AA:BB:CC:DD:EE:FF"},
                ): str,
                vol.Required(
                    "name",
                    default="BK-Light iPixel",
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
