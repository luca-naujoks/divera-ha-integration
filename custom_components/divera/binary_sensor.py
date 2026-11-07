"""DIVERA alarm flags and locally timed alarm activity."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timezone

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time

from .activity import alarm_bool
from .const import DOMAIN
from .coordinator import DiveraCoordinator
from .entity import DiveraEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DiveraAlarmFlag(coordinator, entry, "priority"),
            DiveraAlarmFlag(coordinator, entry, "closed"),
            DiveraActiveAlarm(coordinator, entry),
        ]
    )


class DiveraAlarmFlag(DiveraEntity, BinarySensorEntity):
    """A boolean API field, unknown when the field or alarm is absent."""

    def __init__(
        self, coordinator: DiveraCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator, entry, key)
        self._key = key

    @property
    def is_on(self) -> bool | None:
        return alarm_bool((self.coordinator.data or {}).get(self._key))


class DiveraActiveAlarm(DiveraEntity, BinarySensorEntity):
    """Reset locally at the stored deadline, even without another API update."""

    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator: DiveraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "active_alarm")
        self._cancel_timer: Callable[[], None] | None = None

    @property
    def is_on(self) -> bool:
        return self.coordinator.activity.is_active(time.time())

    @property
    def extra_state_attributes(self) -> dict:
        activity = self.coordinator.activity
        return {
            "alarm_id": activity.alarm_id,
            "expires_at": (
                datetime.fromtimestamp(activity.expires_at, tz=timezone.utc).isoformat()
                if activity.expires_at is not None
                else None
            ),
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_expiry()

    async def async_will_remove_from_hass(self) -> None:
        self._clear_timer()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._schedule_expiry()
        super()._handle_coordinator_update()

    @callback
    def _clear_timer(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

    @callback
    def _schedule_expiry(self) -> None:
        self._clear_timer()
        deadline = self.coordinator.activity.expires_at
        if deadline is not None and deadline > time.time():
            self._cancel_timer = async_track_point_in_utc_time(
                self.hass,
                self._expire,
                datetime.fromtimestamp(deadline, tz=timezone.utc),
            )

    @callback
    def _expire(self, now: datetime) -> None:
        self._cancel_timer = None
        self.async_write_ha_state()
