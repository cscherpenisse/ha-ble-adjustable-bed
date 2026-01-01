import asyncio
import logging

from bleak import BleakClient, BleakError

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.components.bluetooth import async_ble_device_from_address

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
    """Set up cover entities for the adjustable bed."""
    async_add_entities(
        [
            AdjustableBedCover(
                hass=hass,
                entry=entry,
                name="Head",
                up_cmd=HEAD_UP_CMD,
                down_cmd=HEAD_DOWN_CMD,
            ),
            AdjustableBedCover(
                hass=hass,
                entry=entry,
                name="Feet",
                up_cmd=FEET_UP_CMD,
                down_cmd=FEET_DOWN_CMD,
            ),
        ]
    )


class AdjustableBedCover(CoverEntity):
    """Simulated cover entity for adjustable bed parts."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, hass, entry, name, up_cmd, down_cmd):
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{DEVICE_NAME} {name}"

        self._up_cmd = up_cmd
        self._down_cmd = down_cmd

        self._attr_current_cover_position = 0
        self._is_moving = False

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

    @property
    def is_closed(self):
        """Return True if the cover is closed."""
        if self._attr_current_cover_position is None:
            return None
        return self._attr_current_cover_position == 0

    async def _get_client(self) -> BleakClient:
        """Get or create a persistent BLE client."""
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        if data.get("client") and data["client"].is_connected:
            return data["client"]

        device = async_ble_device_from_address(
            self.hass, data["address"]
        )
        if device is None:
            raise RuntimeError("BLE device not found")

        _LOGGER.debug("Connecting to bed for cover control")

        client = BleakClient(device)
        await client.connect(timeout=15)

        data["client"] = client
        return client

    async def _send_command(self, command_key: str):
        """Send a single BLE command."""
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        async with data["lock"]:
            try:
                client = await self._get_client()
                await client.write_gatt_char(
                    BED_CHAR_UUID,
                    BED_COMMANDS[command_key],
                    response=False,
                )
            except (BleakError, Exception) as err:
                _LOGGER.error(
                    "BLE command failed (%s): %s",
                    command_key,
                    err,
                )
                if data.get("client"):
                    try:
                        await data["client"].disconnect()
                    except Exception:
                        pass
                    data["client"] = None
                raise
async def _move_to_position(self, target: int):
    """Simulate movement to target position without oscillation."""
    if self._is_moving:
        return

    self._is_moving = True

    try:
        target = max(0, min(100, target))
        current = self._attr_current_cover_position

        if current == target:
            return

        moving_up = target > current

        while True:
            if moving_up:
                if self._attr_current_cover_position >= target:
                    break
                await self._send_command(self._up_cmd)
                self._attr_current_cover_position += COVER_MOVE_STEP
            else:
                if self._attr_current_cover_position <= target:
                    break
                await self._send_command(self._down_cmd)
                self._attr_current_cover_position -= COVER_MOVE_STEP

            self._attr_current_cover_position = max(
                0, min(100, self._attr_current_cover_position)
            )

            self.async_write_ha_state()
            await asyncio.sleep(COVER_MOVE_DELAY)

        # Snap exactly to target at the end
        self._attr_current_cover_position = target
        self.async_write_ha_state()

    finally:
        self._is_moving = False

    async def async_open_cover(self, **kwargs):
        """Fully open (raise) the cover."""
        await self._move_to_position(100)

    async def async_close_cover(self, **kwargs):
        """Fully close (lower) the cover."""
        await self._move_to_position(0)

    async def async_set_cover_position(self, **kwargs):
        """Move cover to a specific position."""
        position = kwargs.get("position")
        if position is None:
            return

        await self._move_to_position(position)
