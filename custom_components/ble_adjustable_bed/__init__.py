import asyncio
import logging

from bleak import BleakClient

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import (
    DOMAIN,
    BED_CHAR_UUID,
    BED_COMMANDS,
    BLE_IDLE_DISCONNECT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "cover", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BLE Adjustable Bed from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "address": entry.data["address"],
        "client": None,
        "lock": asyncio.Lock(),
        "disconnect_task": None,
    }

    async def _schedule_disconnect():
        """Schedule BLE disconnect after idle timeout."""
        data = hass.data[DOMAIN][entry.entry_id]

        # Cancel existing disconnect timer
        task = data.get("disconnect_task")
        if task:
            task.cancel()

        async def _disconnect_later():
            try:
                _LOGGER.debug(
                    "Scheduling BLE disconnect in %s seconds",
                    BLE_IDLE_DISCONNECT_TIMEOUT,
                )
                await asyncio.sleep(BLE_IDLE_DISCONNECT_TIMEOUT)

                client = data.get("client")
                if client and client.is_connected:
                    _LOGGER.debug("Disconnecting BLE device (idle timeout)")
                    await client.disconnect()

            except asyncio.CancelledError:
                pass

        data["disconnect_task"] = hass.async_create_task(
            _disconnect_later()
        )

    async def handle_repeat_command(call: ServiceCall) -> None:
        """Repeat a BLE command (used for hold behavior)."""
        command = call.data["command"]
        count = call.data.get("count", 1)
        delay_ms = call.data.get("delay_ms", 300)

        data = hass.data[DOMAIN][entry.entry_id]

        async with data["lock"]:
            device = async_ble_device_from_address(
                hass, data["address"]
            )
            if device is None:
                raise RuntimeError("BLE device not found")

            # Connect if needed
            if not data["client"] or not data["client"].is_connected:
                _LOGGER.debug("Connecting to BLE device")
                data["client"] = BleakClient(device)
                await data["client"].connect(timeout=15)

            # Send commands
            for _ in range(count):
                await data["client"].write_gatt_char(
                    BED_CHAR_UUID,
                    BED_COMMANDS[command],
                    response=False,
                )
                await asyncio.sleep(delay_ms / 1000)

            # Reset idle disconnect timer
            await _schedule_disconnect()

    # Register service for repeat / hold behavior
    hass.services.async_register(
        DOMAIN,
        "repeat_command",
        handle_repeat_command,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)

    if data:
        # Cancel disconnect timer
        task = data.get("disconnect_task")
        if task:
            task.cancel()

        # Disconnect BLE client
        client = data.get("client")
        if client and client.is_connected:
            try:
                await client.disconnect()
            except Exception:
                pass

    await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    hass.data[DOMAIN].pop(entry.entry_id)
    return True
