import logging

from homeassistant.components.select import SelectEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
    PRESETS,
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
        """Apply selected preset via number + cover entities."""
        _LOGGER.info("Preset selected: %s", option)

        data = self.hass.data[DOMAIN][self.entry.entry_id]

        # 1️⃣ Stop active cover movements
        for task in list(data.get("cover_tasks", [])):
            task.cancel()
        data["cover_tasks"].clear()

        # 2️⃣ Find preset config
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

        # 3️⃣ Update number entities (steps)
        if preset.get("head") is not None:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": f"number.{self.entry.entry_id}_head_steps",
                    "value": preset["head"],
                },
                blocking=True,
            )

        if preset.get("feet") is not None:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": f"number.{self.entry.entry_id}_feet_steps",
                    "value": preset["feet"],
                },
                blocking=True,
            )

        # 4️⃣ Trigger cover movement (uses updated numbers)
        if preset.get("head") is not None:
            await self.hass.services.async_call(
                "cover",
                "open_cover",
                {
                    "entity_id": f"cover.{self.entry.entry_id}_head",
                },
                blocking=False,
            )

        if preset.get("feet") is not None:
            await self.hass.services.async_call(
                "cover",
                "open_cover",
                {
                    "entity_id": f"cover.{self.entry.entry_id}_feet",
                },
                blocking=False,
            )

        self._attr_current_option = option
        self.async_write_ha_state()
