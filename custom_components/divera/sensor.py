"""DIVERA 24/7 sensor entity."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UCR_ID, CONF_UCR_NAME, DOMAIN
from .coordinator import DiveraCoordinator
from .entity import DiveraEntity

NO_ALARM_STATE = "Kein aktiver Einsatz"

SENSORS = (
    SensorEntityDescription(key="title", translation_key="title"),
    SensorEntityDescription(key="text", translation_key="text"),
    SensorEntityDescription(key="address", translation_key="address"),
    SensorEntityDescription(key="id", translation_key="id"),
    SensorEntityDescription(
        key="date", translation_key="date", device_class=SensorDeviceClass.TIMESTAMP
    ),
    SensorEntityDescription(key="lat", translation_key="lat"),
    SensorEntityDescription(key="lng", translation_key="lng"),
    SensorEntityDescription(key="vehicles", translation_key="vehicles"),
)


def _fmt_ts(unix: int | None) -> str | None:
    if unix is None:
        return None
    try:
        return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(unix)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        DiveraSensor(coordinator, entry),
        *(DiveraAttributeSensor(coordinator, entry, description) for description in SENSORS),
    ])


class DiveraAttributeSensor(DiveraEntity, SensorEntity):
    """A typed view of one field of the latest alarm."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | int | float | datetime | None:
        alarm = self.coordinator.data
        if alarm is None:
            return None
        key = self.entity_description.key
        value = alarm.get(key)
        if value is None:
            return None
        if key == "date":
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError, OSError):
                return None
        if key in ("lat", "lng"):
            try:
                number = float(value)
                limit = 90 if key == "lat" else 180
                return number if -limit <= number <= limit else None
            except (TypeError, ValueError, OverflowError):
                return None
        if key == "vehicles":
            return len(value) if isinstance(value, (list, dict)) else None
        if key == "id":
            return str(value)[:255]
        return str(value)[:255]

    @property
    def extra_state_attributes(self) -> dict:
        alarm = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "text" and alarm.get(key) is not None:
            return {"full_description": alarm[key]}
        if key == "vehicles" and isinstance(alarm.get(key), (list, dict)):
            return {"vehicles": alarm[key]}
        return {}


class DiveraSensor(CoordinatorEntity[DiveraCoordinator], SensorEntity):

    def __init__(self, coordinator: DiveraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        ucr_name: str = entry.data.get(CONF_UCR_NAME, "DIVERA")
        ucr_id: str = entry.data.get(CONF_UCR_ID, entry.entry_id)

        self._attr_name = f"DIVERA {ucr_name}"
        self._attr_unique_id = f"divera_{ucr_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ucr_id)},
            name=f"DIVERA 24/7 – {ucr_name}",
            manufacturer="DIVERA GmbH",
            model="DIVERA 24/7",
        )

    @property
    def native_value(self) -> str:
        alarm = self.coordinator.data
        if alarm is None:
            return NO_ALARM_STATE
        return alarm.get("title") or NO_ALARM_STATE

    @property
    def extra_state_attributes(self) -> dict:
        alarm = self.coordinator.data
        if alarm is None:
            return {}

        # Gesamten API-Response als Attribute, bekannte Felder mit deutschen Namen
        attrs: dict = {}

        # Bekannte Felder → deutsche Namen
        attrs["stichwort"]    = alarm.get("title")
        attrs["beschreibung"] = alarm.get("text")
        attrs["adresse"]      = alarm.get("address")
        attrs["einsatz_id"]   = alarm.get("id")
        attrs["prioritaet"]   = alarm.get("priority")
        attrs["geschlossen"]  = alarm.get("closed")
        attrs["alarmiert_am"] = _fmt_ts(alarm.get("date"))
        attrs["latitude"]     = alarm.get("lat")
        attrs["longitude"]    = alarm.get("lng")
        attrs["fahrzeuge"]    = alarm.get("vehicles")

        # Alle restlichen API-Felder direkt übernehmen
        bekannte = {"title", "text", "address", "id", "priority", "closed", "date", "lat", "lng", "vehicles"}
        for key, value in alarm.items():
            if key not in bekannte:
                attrs[key] = value

        # None entfernen
        return {k: v for k, v in attrs.items() if v is not None}
