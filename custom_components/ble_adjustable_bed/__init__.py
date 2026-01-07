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
    COVER_MOVE_DELAY_MS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "cover", "number", "sensor", "select"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (register global services)."""
    hass.data.setdefault(DOMAIN, {})

    async def handle_repeat_command(call: ServiceCall) -> None:
        """
        Repeat a BLE command for a specific config entry.
        REQUIRED: entry_id
        """
        entry_id = call.data["entry_id"]
        command = call.data["command"]
        count = call.data.get("count", 1)
        delay_ms = call.data.get("delay_ms", COVER_MOVE_DELAY_MS)

        data = hass.data[DOMAIN].get(entry_id)
        if not data:
            raise ValueError(f"Unknown entry_id: {entry_id}")

        async with data["lock"]:
            device = async_ble_device_from_address(
                hass, data["address"]
            )
            if device is None:
                raise RuntimeError(
                    f"BLE device not found: {data['address']}"
                )

            # Connect if needed
            if not data["client"] or not data["client"].is_connected:
                _LOGGER.debug(
                    "Connecting to BLE device %s",
                    data["address"],
                )
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
            _schedule_disconnect(hass, entry_id)

    hass.services.async_register(
        DOMAIN,
        "repeat_command",
        handle_repeat_command,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up BLE Adjustable Bed from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "address": entry.data["address"],
        "client": None,
        "lock": asyncio.Lock(),
        "disconnect_task": None,
        "cover_tasks": set(),
    }

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True


def _schedule_disconnect(hass: HomeAssistant, entry_id: str) -> None:
    """Schedule BLE disconnect after idle timeout."""
    data = hass.data[DOMAIN][entry_id]

    # Cancel existing disconnect timer
    task = data.get("disconnect_task")
    if task:
        task.cancel()

    async def _disconnect_later():
        try:
            _LOGGER.debug(
                "Scheduling BLE disconnect for %s in %s seconds",
                entry_id,
                BLE_IDLE_DISCONNECT_TIMEOUT,
            )
            await asyncio.sleep(BLE_IDLE_DISCONNECT_TIMEOUT)

            client = data.get("client")
            if client and client.is_connected:
                _LOGGER.debug(
                    "Disconnecting BLE device %s (idle timeout)",
                    data["address"],
                )
                await client.disconnect()
                data["client"] = None

        except asyncio.CancelledError:
            pass

    data["disconnect_task"] = hass.async_create_task(
        _disconnect_later()
    )


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)

    if data:
        # Cancel cover repeat tasks
        for task in list(data.get("cover_tasks", [])):
            task.cancel()

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

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
