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
)

_LOGGER = logging.getLogger(__name__)

# Platforms that this integration provides
PLATFORMS = ["button", "cover"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BLE Adjustable Bed from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "address": entry.data["address"],
        "client": None,
        "lock": asyncio.Lock(),
    }

    async def handle_repeat_command(call: ServiceCall) -> None:
        """Repeat a bed command multiple times (hold button behavior)."""
        command = call.data["command"]
        count = call.data.get("count", 5)
        delay_ms = call.data.get("delay_ms", 300)

        data = hass.data[DOMAIN][entry.entry_id]

        async with data["lock"]:
            device = async_ble_device_from_address(
                hass, data["address"]
            )
            if device is None:
                raise RuntimeError("BLE device not found")

            if not data["client"] or not data["client"].is_connected:
                _LOGGER.debug("Connecting to adjustable bed (repeat command)")
                data["client"] = BleakClient(device)
                await data["client"].connect(timeout=15)

            for _ in range(count):
                await data["client"].write_gatt_char(
                    BED_CHAR_UUID,
                    BED_COMMANDS[command],
                    response=False,
                )
                await asyncio.sleep(delay_ms / 1000)

    # Register service for hold / repeat behavior
    hass.services.async_register(
        DOMAIN,
        "repeat_command",
        handle_repeat_command,
    )

    # Forward setup to platforms (button, cover)
    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)

    # Disconnect BLE client if connected
    if data and data.get("client"):
        try:
            await data["client"].disconnect()
        except Exception:
            pass

    # Unload platforms
    await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    hass.data[DOMAIN].pop(entry.entry_id)
    return True
