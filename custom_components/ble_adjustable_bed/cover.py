import asyncio
import logging

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)

from .const import (
    DOMAIN,
    DEVICE_NAME,
    MANUFACTURER,
    MODEL,
    BED_CHAR_UUID,
    BED_COMMANDS,
    COVER_MOVE_STEP,
    COVER_MOVE_DELAY,
    HEAD_UP_CMD,
    HEAD_DOWN_CMD,
    FEET_UP_CMD,
    FEET_DOWN_CMD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        AdjustableBedCover(
            hass, entry,
            name="Head",
            up_cmd=HEAD_UP_CMD,
            down_cmd=HEAD_DOWN_CMD,
        ),
        AdjustableBedCover(
            hass, entry,
            name="Feet",
            up_cmd=FEET_UP_CMD,
            down_cmd=FEET_DOWN_CMD,
        ),
    ])


class AdjustableBedCover(CoverEntity):
    _attr_supported_features = (
        CoverEntityFeature.OPEN |
        CoverEntityFeature.CLOSE |
        CoverEntityFeature.SET_POSITION
    )

    def __init__(self, hass, entry, name, up_cmd, down_cmd):
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{DEVICE_NAME} {name}"
        self._attr_current_cover_position = 0
        self._moving = False
        self._up_cmd = up_cmd
        self._down_cmd = down_cmd

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    async def _send(self, command):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        async with data["lock"]:
            client = data["client"]
            if not client or not client.is_connected:
                from bleak import BleakClient
                from homeassistant.components.bluetooth import async_ble_device_from_address
                device = async_ble_device_from_address(
                    self.hass, data["address"]
                )
                client = BleakClient(device)
                await client.connect()
                data["client"] = client

            await client.write_gatt_char(
                BED_CHAR_UUID,
                BED_COMMANDS[command],
                response=False,
            )

    async def _move_to(self, target):
        if self._moving:
            return

        self._moving = True

        try:
            while self._attr_current_cover_position != target:
                if self._attr_current_cover_position < target:
                    await self._send(self._up_cmd)
                    self._attr_current_cover_position += COVER_MOVE_STEP
                else:
                    await self._send(self._down_cmd)
                    self._attr_current_cover_position -= COVER_MOVE_STEP

                self._attr_current_cover_position = max(
                    0, min(100, self._attr_current_cover_position)
                )

                self.async_write_ha_state()
                await asyncio.sleep(COVER_MOVE_DELAY)
        finally:
            self._moving = False

    async def async_open_cover(self, **kwargs):
        await self._move_to(100)

    async def async_close_cover(self, **kwargs):
        await self._move_to(0)

    async def async_set_cover_position(self, **kwargs):
        position = kwargs.get("position")
        await self._move_to(position)
