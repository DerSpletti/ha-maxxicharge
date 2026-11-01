"""Maxxicharge: aufgeräumte, geprüfte Anbindung der Maxxisun-CCU2 über MQTT."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import mqtt, panel_custom
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from .bus import BrokerConflict, EmbeddedBus, HaBus, get_manager
from .const import (
    CONF_KIND,
    KIND_CCU,
    KIND_TOTAL,
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
from .total import TotalCoordinator
from .discovery import async_collect, specs_from_json, specs_to_json
from .watcher import async_start_watcher

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_URL = "/maxxicharge/maxxicharge-card.js"
PANEL_URL = "/maxxicharge/maxxicharge-panel.js"
TOTAL_PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]

type MaxxiConfigEntry = ConfigEntry[MaxxiCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Karte für das Dashboard bereitstellen (eine Datei, keine Abhängigkeiten)."""
    try:
        integration = await async_get_integration(hass, DOMAIN)
        path = Path(__file__).parent / "frontend" / "maxxicharge-card.js"
        await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(path), False)])
        add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")
        panel = Path(__file__).parent / "frontend" / "maxxicharge-panel.js"
        await hass.http.async_register_static_paths([StaticPathConfig(PANEL_URL, str(panel), False)])
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="maxxicharge-panel",
            frontend_url_path="maxxicharge",
            module_url=f"{PANEL_URL}?v={integration.version}",
            sidebar_title="Maxxicharge",
            sidebar_icon="mdi:solar-power-variant",
            require_admin=False,
            config={},
        )
    except Exception:  # noqa: BLE001 - Karte und Seite sind optional, die Integration läuft auch ohne
        _LOGGER.warning("Maxxicharge-Karte oder -Seite konnte nicht bereitgestellt werden", exc_info=True)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
    """Eintrag einrichten: Gesamtübersicht oder eine CCU."""
    if entry.data.get(CONF_KIND, KIND_CCU) == KIND_TOTAL:
        return await _async_setup_total(hass, entry)
    return await _async_setup_ccu(hass, entry)


async def _async_setup_total(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = TotalCoordinator(hass, entry)
    await coordinator.async_start()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_stop)
    await hass.config_entries.async_forward_entry_setups(entry, TOTAL_PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_setup_ccu(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
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
    if not any(e.data.get(CONF_KIND) == KIND_TOTAL for e in hass.config_entries.async_entries(DOMAIN)):
        hass.async_create_task(  # Gesamtübersicht einmalig anlegen (Duplikate bricht der Flow ab)
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "total"}, data={CONF_KIND: KIND_TOTAL}
            )
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MaxxiConfigEntry) -> bool:
    platforms = TOTAL_PLATFORMS if entry.data.get(CONF_KIND) == KIND_TOTAL else PLATFORMS
    return await hass.config_entries.async_unload_platforms(entry, platforms)


async def _async_reload(hass: HomeAssistant, entry: MaxxiConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
