"""Maxxicharge: aufgeräumte, geprüfte Anbindung der Maxxisun-CCU2 über MQTT."""

from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.storage import Store

from .bus import BrokerConflict, EmbeddedBus, HaBus, get_manager
from .const import (
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_USER,
    CONF_CCU_ID,
    CONF_MODE,
    CONF_PREFIX,
    DEFAULT_PREFIX,
    DISCOVERY_TIMEOUT,
    DOMAIN,
    EMBEDDED_WAIT,
    MODE_EMBEDDED,
    MODE_HA,
)
from .coordinator import MaxxiCoordinator
from .discovery import async_collect, specs_from_json, specs_to_json
from .watcher import async_start_watcher

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
    """CCU einrichten: Nachrichtenweg wählen, Discovery lesen, Entities anlegen."""
    ccu_id = entry.data[CONF_CCU_ID]
    prefix = entry.data.get(CONF_PREFIX, DEFAULT_PREFIX)
    mode = entry.data.get(CONF_MODE, MODE_HA)

    if mode == MODE_EMBEDDED:
        port = entry.data[CONF_BROKER_PORT]
        manager = get_manager(hass)
        try:
            broker = await manager.acquire(
                entry.entry_id, port, entry.data[CONF_BROKER_USER], entry.data[CONF_BROKER_PASSWORD]
            )
        except (OSError, BrokerConflict) as err:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="port_in_use",
                translation_placeholders={"port": str(port)},
            ) from err
        entry.async_on_unload(lambda: manager.release(entry.entry_id))
        bus = EmbeddedBus(broker)
    else:
        mqtt_entries = hass.config_entries.async_entries("mqtt")
        if not mqtt_entries or not (
            any(e.state is ConfigEntryState.LOADED for e in mqtt_entries)
            or await mqtt.async_wait_for_mqtt_client(hass)
        ):
            raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="mqtt_not_ready")
        bus = HaBus(hass)

    store = Store(hass, 1, f"{DOMAIN}.{ccu_id}")
    cached = await store.async_load()
    # Ohne gespeicherte Entities beim eingebauten Broker länger auf die erste Meldung der CCU warten
    wait = EMBEDDED_WAIT if (mode == MODE_EMBEDDED and not cached) else DISCOVERY_TIMEOUT
    specs = (await async_collect(bus, prefix, ccu_id, wait)).get(ccu_id)
    if specs:
        await store.async_save(specs_to_json(specs))
    else:  # CCU hat sich noch nicht gemeldet: zuletzt bekannte Entities verwenden
        specs = specs_from_json(cached) if cached else None
        if specs:
            _LOGGER.info("CCU %s hat sich noch nicht gemeldet, nutze gespeicherte Entities", ccu_id)
    if not specs:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ccu_not_found",
            translation_placeholders={"ccu": ccu_id},
        )

    coordinator = MaxxiCoordinator(hass, entry, specs, bus)
    await coordinator.async_start()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_stop)
    entry.async_on_unload(await async_start_watcher(hass, entry, bus, prefix))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    _LOGGER.info("CCU %s eingerichtet (%s) mit %d Entities", ccu_id, mode, len(specs))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: MaxxiConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
