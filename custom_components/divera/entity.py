"""Shared DIVERA device identity for all alarm entities."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UCR_ID, CONF_UCR_NAME, DOMAIN
from .coordinator import DiveraCoordinator


class DiveraEntity(CoordinatorEntity[DiveraCoordinator]):
    """An entity belonging to the configured DIVERA unit."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DiveraCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        ucr_name = entry.data.get(CONF_UCR_NAME, "DIVERA")
        ucr_id = entry.data.get(CONF_UCR_ID, entry.entry_id)
        self._attr_unique_id = f"divera_{ucr_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ucr_id)},
            name=f"DIVERA 24/7 – {ucr_name}",
            manufacturer="DIVERA GmbH",
            model="DIVERA 24/7",
        )
