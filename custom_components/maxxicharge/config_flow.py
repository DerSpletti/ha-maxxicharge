"""Einrichtungsassistent: MQTT klären, CCUs finden, auswählen, alte Entities aufräumen."""

from __future__ import annotations

import ipaddress
import logging
import re
import secrets
import string
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .bus import BrokerConflict, EmbeddedBus, HaBus, get_manager
from .const import (
    CLEANUP_DISABLE,
    CLEANUP_ENABLE,
    CLEANUP_NONE,
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_USER,
    CONF_CCU_ID,
    CONF_CCUS,
    CONF_CLEANUP,
    CONF_IP,
    CONF_MODE,
    CONF_PREFIX,
    DEFAULT_BROKER_PORT,
    DEFAULT_BROKER_USER,
    DEFAULT_PREFIX,
    DOMAIN,
    MODE_EMBEDDED,
    MODE_HA,
)
from .discovery import Spec, async_collect

_LOGGER = logging.getLogger(__name__)
CCU_RE = re.compile(r"^CCU2-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$")
USER_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
PW_RE = re.compile(r"^[A-Za-z0-9_.-]{8,64}$")


async def _check_ip(hass: HomeAssistant, ip: str) -> bool:
    """Optionalen lokalen Endpunkt http://<ip>/api/live prüfen."""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    try:
        async with async_get_clientsession(hass).get(
            f"http://{ip}/api/live", timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            return resp.status == 200 and isinstance(await resp.json(content_type=None), dict)
    except (aiohttp.ClientError, TimeoutError, ValueError):
        return False


def cleanup_autodiscovery(hass: HomeAssistant, ccu_id: str, mode: str) -> int:
    """Alte MQTT-Autodiscovery-Entities der CCU deaktivieren bzw. wieder aktivieren.

    Es wird nichts gelöscht. Wieder aktiviert werden nur Entities, die per Nutzer-
    Deaktivierung abgeschaltet sind (also auch die von uns deaktivierten).
    """
    if mode not in (CLEANUP_DISABLE, CLEANUP_ENABLE):
        return 0
    dev_reg, ent_reg = dr.async_get(hass), er.async_get(hass)
    count = 0
    for device in list(dev_reg.devices.values()):
        if not any(i[0] == "mqtt" and ccu_id.lower() in str(i[1]).lower() for i in device.identifiers):
            continue
        for ent in er.async_entries_for_device(ent_reg, device.id, include_disabled_entities=True):
            if ent.platform != "mqtt":
                continue
            if mode == CLEANUP_DISABLE and ent.disabled_by is None:
                ent_reg.async_update_entity(ent.entity_id, disabled_by=er.RegistryEntryDisabler.USER)
                count += 1
            elif mode == CLEANUP_ENABLE and ent.disabled_by == er.RegistryEntryDisabler.USER:
                ent_reg.async_update_entity(ent.entity_id, disabled_by=None)
                count += 1
    _LOGGER.info("Aufräumen (%s) für %s: %d Entities geändert", mode, ccu_id, count)
    return count


async def _mqtt_ready(hass: HomeAssistant) -> bool:
    """MQTT ist in Home Assistant eingerichtet und geladen."""
    entries = hass.config_entries.async_entries("mqtt")
    if not entries:
        return False
    if any(e.state is ConfigEntryState.LOADED for e in entries):
        return True
    try:
        return bool(await mqtt.async_wait_for_mqtt_client(hass))
    except Exception:  # noqa: BLE001
        return False


async def _host_ip(hass: HomeAssistant) -> str:
    try:
        from homeassistant.components.network import async_get_source_ip

        return await async_get_source_ip(hass)
    except Exception:  # noqa: BLE001
        return "<IP von Home Assistant>"


async def _ha_broker_info(hass: HomeAssistant) -> dict[str, str]:
    """Broker-Daten der HA-MQTT-Integration, so dass die CCU sie erreicht."""
    host: str | None = None
    port = 1883
    entries = hass.config_entries.async_entries("mqtt")
    if entries:
        host = entries[0].data.get("broker")
        port = entries[0].data.get("port", 1883)
    # Add-on-Namen und Loopback kann die CCU nicht auflösen: dann die IP von Home Assistant
    if not host or "." not in host or host.startswith("127."):
        host = await _host_ip(hass)
    return {"broker": str(host), "port": str(port), "user": "", "password": "", "rejected": "–", "connected": "–"}


def _label(ccu_id: str, specs: dict[str, Spec]) -> str:
    model = next((s.model for s in specs.values() if s.model), "CCU")
    return f"{ccu_id} ({model}, {len(specs)} Entities)"


def _random_password() -> str:
    """Zufallspasswort ohne leicht verwechselbare Zeichen (kein 0/O, 1/l/I), gut abtippbar."""
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(12))


class MaxxiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Assistent: MQTT klären → CCU verbinden → CCUs suchen → auswählen."""

    VERSION = 1

    def __init__(self) -> None:
        self._prefix = DEFAULT_PREFIX
        self._mode = MODE_HA
        self._emb: dict[str, Any] = {}
        self._pw = _random_password()
        self._found: dict[str, dict[str, Spec]] = {}
        self._disc: dict[str, Any] = {}
        self._ph: dict[str, str] = {"broker": "?", "port": "1883", "user": "", "password": "", "rejected": "–", "connected": "–"}

    # ---------- Hilfen ----------
    def _existing_embedded(self) -> dict[str, Any] | None:
        for e in self._async_current_entries():
            if e.data.get(CONF_MODE) == MODE_EMBEDDED:
                return {k: e.data[k] for k in (CONF_BROKER_PORT, CONF_BROKER_USER, CONF_BROKER_PASSWORD)}
        return None

    def _conn_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {CONF_MODE: self._mode, CONF_PREFIX: self._prefix, CONF_IP: ""}
        if self._mode == MODE_EMBEDDED:
            data.update(self._emb)
        return data

    async def _ensure_bus(self) -> Any:
        """Nachrichtenweg für die Suche; beim eingebauten Broker wird er dafür gestartet."""
        if self._mode == MODE_EMBEDDED:
            broker = await get_manager(self.hass).acquire(
                self.flow_id,
                self._emb[CONF_BROKER_PORT],
                self._emb[CONF_BROKER_USER],
                self._emb[CONF_BROKER_PASSWORD],
            )
            return EmbeddedBus(broker)
        return HaBus(self.hass)

    @callback
    def async_remove(self) -> None:
        """Assistent beendet: Broker nur freigeben (Einträge halten ihn weiter)."""
        if self._mode == MODE_EMBEDDED:
            get_manager(self.hass).release(self.flow_id)

    async def _scan(self) -> ConfigFlowResult:
        """CCUs suchen und zum passenden Schritt weiterleiten."""
        try:
            bus = await self._ensure_bus()
        except (OSError, BrokerConflict):
            return self.async_abort(reason="port_in_use")
        found = await async_collect(bus, self._prefix)
        configured = {e.data.get(CONF_CCU_ID) for e in self._async_current_entries()}
        self._found = {k: v for k, v in found.items() if k not in configured}
        if self._found:
            return await self.async_step_select()
        if found:
            return self.async_abort(reason="already_configured")
        if self._mode == MODE_EMBEDDED:
            broker = get_manager(self.hass).broker
            rejected = broker.recent_rejections() if broker else []
            self._ph = {
                **self._ph,
                "rejected": ", ".join(rejected) or "–",
                "connected": ", ".join(broker.connected_clients()) if broker else "–",
            }
            self._ph["connected"] = self._ph["connected"] or "–"
        return await self.async_step_no_ccu()

    async def async_step_no_ccu(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Menü: keine CCU gefunden."""
        return self.async_show_menu(
            step_id="no_ccu", menu_options=["retry", "manual"], description_placeholders=self._ph
        )

    # ---------- Einstieg ----------
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Willkommensseite: was man für die Einrichtung braucht (IP, Port, Benutzer, Passwort)."""
        if user_input is not None:
            return await self.async_step_connect()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={"ha_ip": await _host_ip(self.hass)},
        )

    async def async_step_connect(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if await _mqtt_ready(self.hass):
            self._mode = MODE_HA
            self._ph = await _ha_broker_info(self.hass)
            if user_input is not None:
                self._prefix = user_input[CONF_PREFIX].strip().strip("/") or DEFAULT_PREFIX
                return await self._scan()
            return self.async_show_form(
                step_id="connect",
                data_schema=vol.Schema({vol.Required(CONF_PREFIX, default=DEFAULT_PREFIX): str}),
                description_placeholders=self._ph,
            )
        existing = self._existing_embedded()
        if existing:  # eingebauter Broker läuft schon für andere CCUs
            self._mode, self._emb = MODE_EMBEDDED, existing
            return await self.async_step_search()
        return await self.async_step_broker_choice()

    async def async_step_broker_choice(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Menü: eingebauter Broker oder eigenes MQTT."""
        return self.async_show_menu(
            step_id="broker_choice", menu_options=["embedded", "mqtt_missing"]
        )

    async def async_step_mqtt_missing(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Nutzer will ein eigenes MQTT: erklären, dann erneut prüfen."""
        if user_input is not None:
            return await self.async_step_connect()
        return self.async_show_form(step_id="mqtt_missing", data_schema=vol.Schema({}))

    # ---------- Eingebauter Broker ----------
    async def async_step_embedded(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            port = int(user_input[CONF_BROKER_PORT])
            user, pw = user_input[CONF_BROKER_USER], user_input[CONF_BROKER_PASSWORD]
            if not USER_RE.match(user):
                errors[CONF_BROKER_USER] = "invalid_user"
            elif not PW_RE.match(pw):
                errors[CONF_BROKER_PASSWORD] = "invalid_password"
            else:
                self._mode = MODE_EMBEDDED
                self._emb = {CONF_BROKER_PORT: port, CONF_BROKER_USER: user, CONF_BROKER_PASSWORD: pw}
                try:
                    await get_manager(self.hass).acquire(self.flow_id, port, user, pw)
                except (OSError, BrokerConflict):
                    errors[CONF_BROKER_PORT] = "port_in_use"
                else:
                    return await self.async_step_search()
        return self.async_show_form(
            step_id="embedded",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BROKER_PORT, default=DEFAULT_BROKER_PORT): vol.All(
                        vol.Coerce(int), vol.Range(min=1024, max=65535)
                    ),
                    vol.Required(CONF_BROKER_USER, default=DEFAULT_BROKER_USER): str,
                    vol.Required(CONF_BROKER_PASSWORD, default=self._pw): str,
                }
            ),
            errors=errors,
        )

    async def async_step_search(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Anleitung für die CCU (eingebauter Broker) und Suche."""
        self._ph = {
            "broker": await _host_ip(self.hass),
            "port": str(self._emb[CONF_BROKER_PORT]),
            "user": self._emb[CONF_BROKER_USER],
            "password": self._emb[CONF_BROKER_PASSWORD],
            "rejected": "–",
            "connected": "–",
        }
        if user_input is not None:
            return await self._scan()
        return self.async_show_form(
            step_id="search", data_schema=vol.Schema({}), description_placeholders=self._ph
        )

    async def async_step_retry(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Erneut nach CCUs suchen."""
        return await self._scan()

    # ---------- Auswahl ----------
    async def async_step_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = {k: _label(k, v) for k, v in self._found.items()}
        if user_input is not None:
            ids = list(user_input[CONF_CCUS])
            if not ids:
                return self.async_show_form(
                    step_id="select",
                    data_schema=self._select_schema(options),
                    errors={"base": "none_selected"},
                )
            for other in ids[1:]:  # weitere CCUs als eigene Einträge anlegen
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "ccu"},
                        data={**self._conn_data(), CONF_CCU_ID: other},
                    )
                )
            return await self.async_step_ccu({**self._conn_data(), CONF_CCU_ID: ids[0]})
        return self.async_show_form(step_id="select", data_schema=self._select_schema(options))

    @staticmethod
    def _select_schema(options: dict[str, str]) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_CCUS, default=list(options)): cv.multi_select(options)})

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            ccu_id = user_input[CONF_CCU_ID].strip().upper()
            ip = (user_input.get(CONF_IP) or "").strip()
            if not CCU_RE.match(ccu_id):
                errors[CONF_CCU_ID] = "invalid_ccu_id"
            elif ip and not await _check_ip(self.hass, ip):
                errors[CONF_IP] = "cannot_connect"
            else:
                try:
                    bus = await self._ensure_bus()
                except (OSError, BrokerConflict):
                    return self.async_abort(reason="port_in_use")
                if ccu_id not in await async_collect(bus, self._prefix, ccu_id):
                    errors["base"] = "not_found"
                else:
                    return await self.async_step_ccu({**self._conn_data(), CONF_CCU_ID: ccu_id, CONF_IP: ip})
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CCU_ID): str,
                    vol.Optional(CONF_IP, default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_integration_discovery(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Eine unbekannte CCU hat sich am Broker gemeldet (Hintergrund-Erkennung)."""
        await self.async_set_unique_id(data[CONF_CCU_ID])
        self._abort_if_unique_id_configured()
        self._disc = dict(data)
        self.context["title_placeholders"] = {"name": f"CCU {data[CONF_CCU_ID][-4:]}"}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=f"CCU {self._disc[CONF_CCU_ID][-4:]}", data=self._disc)
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"ccu": self._disc[CONF_CCU_ID]},
        )

    async def async_step_ccu(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Eintrag für eine CCU anlegen (auch von weiteren Flows genutzt)."""
        await self.async_set_unique_id(data[CONF_CCU_ID])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=f"CCU {data[CONF_CCU_ID][-4:]}", data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MaxxiOptionsFlow()


class MaxxiOptionsFlow(OptionsFlow):
    """Optionen: Verbindungsdaten ansehen, Passwort ändern, IP setzen, alte Entities aufräumen."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = ["connection", "settings"]
        if self.config_entry.data.get(CONF_MODE) == MODE_EMBEDDED:
            options.append("password")
        return self.async_show_menu(step_id="init", menu_options=options)

    async def async_step_connection(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self.config_entry.data.get(CONF_MODE) == MODE_EMBEDDED:
            return await self.async_step_connection_embedded()
        return await self.async_step_connection_ha()

    async def async_step_connection_embedded(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Zugangsdaten des eingebauten Brokers anzeigen (für die Maxxisun-App)."""
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options))
        d = self.config_entry.data
        return self.async_show_form(
            step_id="connection_embedded",
            data_schema=vol.Schema({}),
            description_placeholders={
                "broker": await _host_ip(self.hass),
                "port": str(d[CONF_BROKER_PORT]),
                "user": d[CONF_BROKER_USER],
                "password": d[CONF_BROKER_PASSWORD],
            },
        )

    async def async_step_connection_ha(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Broker-Daten des vorhandenen MQTT anzeigen (Passwort kennt die Integration nicht)."""
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options))
        return self.async_show_form(
            step_id="connection_ha",
            data_schema=vol.Schema({}),
            description_placeholders=await _ha_broker_info(self.hass),
        )

    async def async_step_password(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Passwort des eingebauten Brokers ändern (gilt für alle CCUs)."""
        errors: dict[str, str] = {}
        entry = self.config_entry
        if user_input is not None:
            pw = user_input[CONF_BROKER_PASSWORD]
            if not PW_RE.match(pw):
                errors[CONF_BROKER_PASSWORD] = "invalid_password"
            else:
                try:
                    await get_manager(self.hass).async_replace(
                        entry.data[CONF_BROKER_PORT], entry.data[CONF_BROKER_USER], pw
                    )
                except OSError:
                    errors["base"] = "port_in_use"
                else:
                    for e in self.hass.config_entries.async_entries(DOMAIN):
                        if e.data.get(CONF_MODE) == MODE_EMBEDDED:
                            self.hass.config_entries.async_update_entry(
                                e, data={**e.data, CONF_BROKER_PASSWORD: pw}
                            )
                    return self.async_create_entry(data=dict(entry.options))
        return self.async_show_form(
            step_id="password",
            data_schema=vol.Schema({vol.Required(CONF_BROKER_PASSWORD, default=_random_password()): str}),
            errors=errors,
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self.config_entry
        current_ip = entry.options.get(CONF_IP, entry.data.get(CONF_IP, ""))
        if user_input is not None:
            ip = (user_input.get(CONF_IP) or "").strip()
            if ip and not await _check_ip(self.hass, ip):
                errors[CONF_IP] = "cannot_connect"
            else:
                cleanup_autodiscovery(
                    self.hass, entry.data[CONF_CCU_ID], user_input.get(CONF_CLEANUP, CLEANUP_NONE)
                )
                return self.async_create_entry(data={CONF_IP: ip})
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_IP, default=current_ip): str,
                    vol.Required(CONF_CLEANUP, default=CLEANUP_NONE): SelectSelector(
                        SelectSelectorConfig(
                            options=[CLEANUP_NONE, CLEANUP_DISABLE, CLEANUP_ENABLE],
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="cleanup",
                        )
                    ),
                }
            ),
            errors=errors,
        )
