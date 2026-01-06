from homeassistant.components.sensor import SensorEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
         BleConnectionSensor(hass, entry),
         ActiveStepsSensor(hass, entry),
        ]
    )


class BleConnectionSensor(SensorEntity):
    """Sensor showing BLE connection status."""

    _attr_has_entity_name = True
    _attr_name = "Bluetooth Connection"
    _attr_icon = "mdi:bluetooth"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ble_connection"

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

    @property
    def native_value(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        client = data.get("client")

        if client and client.is_connected:
            return "connected"

        return "disconnected"

class ActiveStepsSensor(SensorEntity):
    """Debug sensor showing active steps sent to the bed."""

    _attr_has_entity_name = True
    _attr_name = "Active Steps"
    _attr_icon = "mdi:counter"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_steps"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("name", DEVICE_NAME),
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        active = data.get("active_steps", {})

        if not active:
            return 0

        # show max of head/feet for clarity
        return max(active.values())
