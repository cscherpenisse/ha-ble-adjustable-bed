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
    HEAD_UP_CMD,
    HEAD_DOWN_CMD,
    FEET_UP_CMD,
    FEET_DOWN_CMD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            AdjustableBedCover(
                hass,
                entry,
                name="Head",
                up_cmd=HEAD_UP_CMD,
                down_cmd=HEAD_DOWN_CMD,
                steps_entity="number.bed_head_steps",
            ),
            AdjustableBedCover(
                hass,
                entry,
                name="Feet",
                up_cmd=FEET_UP_CMD,
                down_cmd=FEET_DOWN_CMD,
                steps_entity="number.bed_feet_steps",
            ),
        ]
    )


class AdjustableBedCover(CoverEntity):
    """Cover without position, step-based movement."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    )

    def __init__(self, hass, entry, name, up_cmd, down_cmd, steps_entity):
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{DEVICE_NAME} {name}"
        self._up_cmd = up_cmd
        self._down_cmd = down_cmd
        self._steps_entity = steps_entity

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    def _get_steps(self) -> int:
        state = self.hass.states.get(self._steps_entity)
        if state and state.state.isdigit():
            return int(state.state)
        return 10  # fallback

    async def _repeat(self, command):
        steps = self._get_steps()
        _LOGGER.debug("Moving %s %d steps", command, steps)

        await self.hass.services.async_call(
            DOMAIN,
            "repeat_command",
            {
                "command": command,
                "count": steps,
                "delay_ms": 150,
            },
            blocking=True,
        )

    async def async_open_cover(self, **kwargs):
        await self._repeat(self._up_cmd)

    async def async_close_cover(self, **kwargs):
        await self._repeat(self._down_cmd)

    @property
    def is_closed(self):
        return None  # unknown / optimistic
