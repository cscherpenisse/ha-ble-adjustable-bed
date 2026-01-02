from homeassistant.components.number import NumberEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    data.setdefault("numbers", {})

    head = BedStepsNumber(entry, "Head Steps", "head")
    feet = BedStepsNumber(entry, "Feet Steps", "feet")

    data["numbers"]["head"] = head
    data["numbers"]["feet"] = feet

    async_add_entities([head, feet])



class BedStepsNumber(NumberEntity):
    """Number entity to control amount of movement steps."""

    _attr_min_value = 1
    _attr_max_value = 100
    _attr_step = 1
    _attr_mode = "box"

    def __init__(self, entry, name, key):
        self.entry = entry
        self.key = key
        self._attr_name = f"{DEVICE_NAME} {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}_steps"
        self._attr_native_value = 100


    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Handle value updates from Home Assistant."""
        self._attr_native_value = int(value)
        self.async_write_ha_state()
