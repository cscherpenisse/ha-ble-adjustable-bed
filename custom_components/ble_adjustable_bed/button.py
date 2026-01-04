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

    # Bed command buttons
    for key, command in BED_COMMANDS.items():
        buttons.append(
            AdjustableBedButton(
                hass=hass,
                entry=entry,
                key=key,
                name=key.replace("_", " ").title(),
            )
        )

    # Stop button
    buttons.append(
        AdjustableBedStopButton(
            hass=hass,
            entry=entry,
        )
    )

    async_add_entities(buttons)


class AdjustableBedButton(ButtonEntity):
    _attr_icon = "mdi:bed"
    _attr_has_entity_name = True

    def __init__(self, hass, entry, key, name):
        self.hass = hass
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"

        data = hass.data[DOMAIN][entry.entry_id]

        if data.get("lock") is None:
            data["lock"] = asyncio.Lock()

        if data.get("cover_tasks") is None:
            data["cover_tasks"] = set()

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
                if data.get("client"):
                    try:
                        await data["client"].disconnect()
                    except Exception:
                        pass
                    data["client"] = None
                raise


class AdjustableBedStopButton(ButtonEntity):
    """Stop button that cancels all cover repeat tasks and disconnects BLE."""

    _attr_has_entity_name = True
    _attr_name = "Stop"
    _attr_icon = "mdi:stop-circle"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stop"

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

    async def async_press(self) -> None:
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        _LOGGER.info("Stop button pressed: cancelling cover tasks")

        # 1️⃣ Cancel ALL cover repeat tasks
        tasks = data.get("cover_tasks", set())
        for task in list(tasks):
            task.cancel()

        tasks.clear()

        # 2️⃣ Cancel pending disconnect timer
        disconnect_task = data.get("disconnect_task")
        if disconnect_task:
            disconnect_task.cancel()
            data["disconnect_task"] = None

        # 3️⃣ Disconnect BLE immediately
        client = data.get("client")
        if client and client.is_connected:
            _LOGGER.info("Disconnecting BLE after stop")
            await client.disconnect()
            data["client"] = None
