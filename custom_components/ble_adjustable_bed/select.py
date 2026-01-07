import logging

from homeassistant.components.select import SelectEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
    PRESETS,
    HEAD_UP_CMD,
    FEET_UP_CMD,
    COVER_MOVE_DELAY_MS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [AdjustableBedPresetSelect(hass, entry)]
    )


class AdjustableBedPresetSelect(SelectEntity):
    """Preset selector for adjustable bed."""

    _attr_has_entity_name = True
    _attr_name = "Preset"
    _attr_icon = "mdi:playlist-check"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_preset"
        self._attr_options = [
            preset["name"] for preset in PRESETS.values()
        ]
        self._attr_current_option = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("name", DEVICE_NAME),
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "connections": {
                ("bluetooth", self.entry.data["address"])
            },
        }

    async def async_select_option(self, option: str) -> None:
        """Apply selected preset."""
        _LOGGER.info("Preset selected: %s", option)

        data = self.hass.data[DOMAIN][self.entry.entry_id]

        # Stop active cover movements
        for task in list(data.get("cover_tasks", [])):
            task.cancel()
        data["cover_tasks"].clear()

        # Find preset config
        preset = next(
            (
                p for p in PRESETS.values()
                if p["name"] == option
            ),
            None,
        )

        if not preset:
            _LOGGER.warning("Unknown preset: %s", option)
            return

        # Apply head movement
        if preset.get("head") is not None:
            await self.hass.services.async_call(
                DOMAIN,
                "repeat_command",
                {
                    "entry_id": self.entry.entry_id,
                    "command": HEAD_UP_CMD,
                    "count": preset["head"],
                    "delay_ms": COVER_MOVE_DELAY_MS,
                },
                blocking=False,
            )

        # Apply feet movement
        if preset.get("feet") is not None:
            await self.hass.services.async_call(
                DOMAIN,
                "repeat_command",
                {
                    "entry_id": self.entry.entry_id,
                    "command": FEET_UP_CMD,
                    "count": preset["feet"],
                    "delay_ms": COVER_MOVE_DELAY_MS,
                },
                blocking=False,
            )

        self._attr_current_option = option
        self.async_write_ha_state()
