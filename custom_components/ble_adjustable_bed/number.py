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
            BedStepsNumber(
                entry,
                name="Head Steps",
                object_id="bed_head_steps",
            ),
            BedStepsNumber(
                entry,
                name="Feet Steps",
                object_id="bed_feet_steps",
            ),
        ]
    )


class BedStepsNumber(NumberEntity):
    _attr_min_value = 1
    _attr_max_value = 1000
    _attr_step = 1
    _attr_mode = "box"

    def __init__(self, entry, name, object_id):
        self.entry = entry
        self._attr_name = f"{DEVICE_NAME} {name}"
        self._attr_unique_id = f"{entry.entry_id}_{object_id}"
        self._attr_native_value = 10

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
