from homeassistant.components.number import NumberEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            BedStepsNumber(entry, "Head Steps"),
            BedStepsNumber(entry, "Feet Steps"),
        ]
    )


class BedStepsNumber(NumberEntity):
    """Number entity for adjustable bed step control."""

    _attr_min_value = 1
    _attr_max_value = 100
    _attr_step = 1
    _attr_mode = "box"
    _attr_has_entity_name = True

    def __init__(self, entry, name):
        self.entry = entry
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_native_value = 100

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

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = int(value)
        self.async_write_ha_state()
