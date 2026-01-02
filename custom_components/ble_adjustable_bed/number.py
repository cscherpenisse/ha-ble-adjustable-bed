from homeassistant.components.number import NumberEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up number entities for adjustable bed steps."""
    async_add_entities(
        [
            BedStepsNumber(
                entry=entry,
                name="Head Steps",
                entity_id_suffix="head_steps",
            ),
            BedStepsNumber(
                entry=entry,
                name="Feet Steps",
                entity_id_suffix="feet_steps",
            ),
        ]
    )


class BedStepsNumber(NumberEntity):
    """Number entity to control movement steps."""

    _attr_min_value = 1
    _attr_max_value = 1000
    _attr_step = 1
    _attr_mode = "box"
    _attr_has_entity_name = True

    def __init__(self, entry, name: str, entity_id_suffix: str):
        self.entry = entry

        # Display name (shown in UI)
        self._attr_name = name

        # Stable unique ID
        self._attr_unique_id = f"{entry.entry_id}_{entity_id_suffix}"

        # 🔑 EXPLICIETE entity_id (belangrijk!)
        self.entity_id = f"number.adjustable_bed_{entity_id_suffix}"

        # Default value
        self._attr_native_value = 10

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Handle value changes from Home Assistant."""
        self._attr_native_value = int(value)
        self.async_write_ha_state()
