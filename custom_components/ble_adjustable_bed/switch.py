import asyncio
import logging

from bleak import BleakClient, BleakError

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.switch import SwitchEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
    CHARACTERISTIC_UUID,
    POWER_ON_COMMAND,
    POWER_OFF_COMMAND,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            IPixelBKLightPowerSwitch(
                hass,
                entry,
            )
        ]
    )


class IPixelBKLightPowerSwitch(SwitchEntity):
    _attr_icon = "mdi:led"
    _attr_has_entity_name = True

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.address = entry.data["address"]
        self._attr_name = entry.data["name"]
        self._attr_is_on = True  # optimistic

        data = hass.data[DOMAIN][entry.entry_id]
        data["lock"] = asyncio.Lock()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.address)},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "connections": {("bluetooth", self.address)},
        }

    async def _get_client(self) -> BleakClient:
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        if data["client"] and data["client"].is_connected:
            return data["client"]

        device = async_ble_device_from_address(
            self.hass,
            self.address,
        )

        if device is None:
            raise RuntimeError("BLE device not found")

        _LOGGER.debug("Connecting permanently to iPixel %s", self.address)

        client = BleakClient(device)
        await client.connect(timeout=15)

        data["client"] = client
        return client

    async def _send_command(self, command: bytearray):
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        async with data["lock"]:
            try:
                client = await self._get_client()

                await client.write_gatt_char(
                    CHARACTERISTIC_UUID,
                    command,
                    response=False,
                )

            except (BleakError, Exception) as err:
                _LOGGER.error("BLE write failed: %s", err)

                # force reconnect next time
                if data["client"]:
                    try:
                        await data["client"].disconnect()
                    except Exception:
                        pass
                    data["client"] = None

                raise

    async def async_turn_on(self, **kwargs):
        await self._send_command(POWER_ON_COMMAND)
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs):
        await self._send_command(POWER_OFF_COMMAND)
        self._attr_is_on = False
