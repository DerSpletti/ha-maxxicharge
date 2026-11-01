"""Maxxicharge: aufgeräumte, geprüfte Anbindung der Maxxisun-CCU2 über MQTT."""

from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CCU_ID, CONF_PREFIX, DEFAULT_PREFIX, DOMAIN
from .coordinator import MaxxiCoordinator
from .discovery import async_collect

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]

type MaxxiConfigEntry = ConfigEntry[MaxxiCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
    """CCU einrichten: Discovery lesen, abonnieren, Entities anlegen."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="mqtt_not_ready")

    ccu_id = entry.data[CONF_CCU_ID]
    prefix = entry.data.get(CONF_PREFIX, DEFAULT_PREFIX)
    found = await async_collect(hass, prefix, ccu_id)
    specs = found.get(ccu_id)
    if not specs:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ccu_not_found",
            translation_placeholders={"ccu": ccu_id},
        )

    coordinator = MaxxiCoordinator(hass, entry, specs)
    await coordinator.async_start()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    _LOGGER.info("CCU %s eingerichtet mit %d Discovery-Entities", ccu_id, len(specs))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: MaxxiConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
