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
    STEP_MULTIPLIER,
    HEAD_UP_CMD,
    HEAD_DOWN_CMD,
    FEET_UP_CMD,
    FEET_DOWN_CMD,
    COVER_MOVE_DELAY_MS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            AdjustableBedCover(
                hass=hass,
                entry=entry,
                name="Head",
                up_cmd=HEAD_UP_CMD,
                down_cmd=HEAD_DOWN_CMD,
                steps_key="head",
            ),
            AdjustableBedCover(
                hass=hass,
                entry=entry,
                name="Feet",
                up_cmd=FEET_UP_CMD,
                down_cmd=FEET_DOWN_CMD,
                steps_key="feet",
            ),
        ]
    )


class AdjustableBedCover(CoverEntity):
    """Step-based adjustable bed cover with STOP support."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    def __init__(self, hass, entry, name, up_cmd, down_cmd, steps_key):
        self.hass = hass
        self.entry = entry
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{name.lower()}"
        self._up_cmd = up_cmd
        self._down_cmd = down_cmd
        self._steps_key = steps_key

        data = hass.data[DOMAIN][entry.entry_id]
        data.setdefault("cover_tasks", set())

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

    def _get_steps(self) -> int:
        entity_id = f"number.adjustable_bed_{self._steps_key}_steps"
        state = self.hass.states.get(entity_id)

        if not state or state.state in ("unknown", "unavailable"):
            return 100 * STEP_MULTIPLIER

        try:
            return int(float(state.state)) * STEP_MULTIPLIER
        except ValueError:
            return 10 * STEP_MULTIPLIER

    async def _repeat(self, command):
        """Start a cancellable repeat task."""
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        steps = self._get_steps()

        async def _runner():
            try:
                await self.hass.services.async_call(
                    DOMAIN,
                    "repeat_command",
                    {
                        "entry_id": self.entry.entry_id,
                        "command": command,
                        "count": steps,
                        "delay_ms": COVER_MOVE_DELAY_MS,
                    },
                    blocking=True,
                )
            except asyncio.CancelledError:
                _LOGGER.debug("Cover movement cancelled")

        task = asyncio.create_task(_runner())
        data["cover_tasks"].add(task)

        task.add_done_callback(
            lambda t: data["cover_tasks"].discard(t)
        )

    async def async_open_cover(self, **kwargs):
        await self._repeat(self._up_cmd)

    async def async_close_cover(self, **kwargs):
        await self._repeat(self._down_cmd)

    async def async_stop_cover(self, **kwargs):
        """Stop movement immediately."""
        data = self.hass.data[DOMAIN][self.entry.entry_id]

        _LOGGER.info(
            "Stopping cover movement for %s",
            self.entry.data.get("name"),
        )

        for task in list(data.get("cover_tasks", [])):
            task.cancel()

        data["cover_tasks"].clear()

    @property
    def is_closed(self):
        """Unknown state (no position feedback)."""
        return None
