import asyncio
import logging

from bleak import BleakClient, BleakError

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.button import ButtonEntity

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
    BED_CHAR_UUID,
    BED_COMMANDS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    buttons = []

    for key, command in BED_COMMANDS.items():
        buttons.append(
            AdjustableBedButton(
                hass=hass,
                entry=entry,
                key=key,
                name=key.replace("_", " ").title(),
            )
        )

    async_add_entities(buttons)


class AdjustableBedButton(ButtonEntity):
    _attr_icon = "mdi:bed"

    def __init__(self, hass, entry, key, name):
        self.hass = hass
        self.entry = entry
        self.key = key
        self._attr_name = name

        data = hass.data[DOMAIN][entry.entry_id]
        if data["lock"] is None:
            data["lock"] = asyncio.Lock()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "connections": {
                ("bluetooth", self.entry.data["address"])
            },
        }

    async def _get_client(self) -> BleakClient:
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        if data["client"] and data["client"].is_connected:
            return data["client"]

        device = async_ble_device_from_address(
            self.hass,
            self.entry.data["address"],
        )

        if device is None:
            raise RuntimeError("BLE device not found")

        _LOGGER.debug(
            "Connecting to adjustable bed %s",
            self.entry.data["address"],
        )

        client = BleakClient(device)
        await client.connect(timeout=15)

        data["client"] = client
        return client

    async def async_press(self) -> None:
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        async with data["lock"]:
            try:
                client = await self._get_client()
                await client.write_gatt_char(
                    BED_CHAR_UUID,
                    BED_COMMANDS[self.key],
                    response=False,
                )
            except (BleakError, Exception) as err:
                _LOGGER.error(
                    "Failed to send bed command %s: %s",
                    self.key,
                    err,
                )
                if data["client"]:
                    try:
                        await data["client"].disconnect()
                    except Exception:
                        pass
                    data["client"] = None
                raise
