from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_ON, STATE_OFF

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [BleConnectionSensor(hass, entry)]
    )


class BleConnectionSensor(SensorEntity):
    """Sensor showing BLE connection status."""

    _attr_has_entity_name = True
    _attr_name = "Bluetooth Connection"
    _attr_icon = "mdi:bluetooth"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_name = name
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
