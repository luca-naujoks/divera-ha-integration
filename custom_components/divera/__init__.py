"""DIVERA 24/7 – Home Assistant Integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DiveraCoordinator

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration einrichten: initiale Daten laden + WebSocket starten."""
    coordinator = DiveraCoordinator(hass, entry)
    await coordinator.async_restore_activity()

    # Initiale Daten per REST laden (blockiert bis Erfolg oder Fehler)
    await coordinator.async_config_entry_first_refresh()

    # Coordinator speichern, bevor Plattformen initialisiert werden
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Sensor-Plattform registrieren
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # WebSocket-Loop als Background-Task starten
    await coordinator.async_start_websocket()

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply timeout changes using the persisted alarm start time."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration entladen: WebSocket stoppen + Plattformen entladen."""
    coordinator: DiveraCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        coordinator.async_stop_websocket()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
