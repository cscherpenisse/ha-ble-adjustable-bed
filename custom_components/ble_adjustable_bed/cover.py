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
    COVER_MOVE_DELAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up cover entities."""
    async_add_entities(
        [
            AdjustableBedCover(
                hass,
                entry,
                name="Head",
                up_cmd=HEAD_UP_CMD,
                down_cmd=HEAD_DOWN_CMD,
                steps_key="head",
            ),
            AdjustableBedCover(
                hass,
                entry,
                name="Feet",
                up_cmd=FEET_UP_CMD,
                down_cmd=FEET_DOWN_CMD,
                steps_key="feet",
            ),
        ]
    )


class AdjustableBedCover(CoverEntity):
    """Adjustable bed cover (no position, step based)."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    )

    def __init__(self, hass, entry, name, up_cmd, down_cmd, steps_key):
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{DEVICE_NAME} {name}"
        self._up_cmd = up_cmd
        self._down_cmd = down_cmd
        self._steps_key = steps_key

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.data["address"])},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    def _get_steps(self) -> int:
        entity_id = f"number.adjustable_bed_{self._steps_key}_steps"
        state = self.hass.states.get(entity_id)

        if not state or state.state in ("unknown", "unavailable"):
            return 100

        try:
            return int(float(state.state))
        except ValueError:
            return 100

    async def _repeat(self, command):
        steps = self._get_steps()
        _LOGGER.debug("Running %s for %d steps", command, steps)

        await self.hass.services.async_call(
            DOMAIN,
            "repeat_command",
            {
                "command": command,
                "count": steps,
                "delay_ms": COVER_MOVE_DELAY,
            },
            blocking=True,
        )

    async def async_open_cover(self, **kwargs):
        await self._repeat(self._up_cmd)

    async def async_close_cover(self, **kwargs):
        await self._repeat(self._down_cmd)

    @property
    def is_closed(self):
        return None
