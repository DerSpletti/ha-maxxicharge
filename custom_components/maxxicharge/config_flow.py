"""Einrichtungsassistent: CCUs am Broker finden, auswählen, alte Entities aufräumen."""

from __future__ import annotations

import ipaddress
import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
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

from .const import (
    CLEANUP_DISABLE,
    CLEANUP_ENABLE,
    CLEANUP_NONE,
    CONF_CCU_ID,
    CONF_CCUS,
    CONF_CLEANUP,
    CONF_IP,
    CONF_PREFIX,
    DEFAULT_PREFIX,
    DOMAIN,
)
from .discovery import Spec, async_collect

_LOGGER = logging.getLogger(__name__)
CCU_RE = re.compile(r"^CCU2-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$")


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

    Es wird nichts gelöscht. Wieder aktiviert werden nur Entities, die der Nutzer-
    Deaktivierung unterliegen (also auch von uns deaktivierte).
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
    """MQTT ist eingerichtet und verbunden."""
    if not hass.config_entries.async_entries("mqtt"):
        return False
    return bool(await mqtt.async_wait_for_mqtt_client(hass))


async def _broker_info(hass: HomeAssistant) -> dict[str, str]:
    """Broker-Daten, die der Nutzer an der CCU eintragen muss (Host so, dass die CCU ihn erreicht)."""
    host: str | None = None
    port = 1883
    entries = hass.config_entries.async_entries("mqtt")
    if entries:
        host = entries[0].data.get("broker")
        port = entries[0].data.get("port", 1883)
    # Add-on-Namen und Loopback kann die CCU nicht auflösen: dann die IP von Home Assistant
    if not host or "." not in host or host.startswith("127."):
        try:
            from homeassistant.components.network import async_get_source_ip

            host = await async_get_source_ip(hass)
        except Exception:  # noqa: BLE001
            host = "<IP von Home Assistant>"
    return {"broker": str(host), "port": str(port)}


def _label(ccu_id: str, specs: dict[str, Spec]) -> str:
    model = next((s.model for s in specs.values() if s.model), "CCU")
    return f"{ccu_id} ({model}, {len(specs)} Entities)"


class MaxxiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Assistent: Suche → Auswahl → fertig."""

    VERSION = 1

    def __init__(self) -> None:
        self._prefix = DEFAULT_PREFIX
        self._found: dict[str, dict[str, Spec]] = {}
        self._ph: dict[str, str] = {"broker": "?", "port": "1883"}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not await _mqtt_ready(self.hass):
            return await self.async_step_mqtt_missing()
        self._ph = await _broker_info(self.hass)
        if user_input is not None:
            self._prefix = user_input[CONF_PREFIX].strip().strip("/") or DEFAULT_PREFIX
            found = await async_collect(self.hass, self._prefix)
            configured = {e.data.get(CONF_CCU_ID) for e in self._async_current_entries()}
            self._found = {k: v for k, v in found.items() if k not in configured}
            if self._found:
                return await self.async_step_select()
            if found:
                return self.async_abort(reason="already_configured")
            return self.async_show_menu(
                step_id="no_ccu",
                menu_options=["retry", "manual"],
                description_placeholders=self._ph,
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PREFIX, default=DEFAULT_PREFIX): str}),
            description_placeholders=self._ph,
        )

    async def async_step_mqtt_missing(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """MQTT fehlt in Home Assistant: erklären, dann erneut prüfen."""
        if user_input is not None:
            return await self.async_step_user()
        return self.async_show_form(step_id="mqtt_missing", data_schema=vol.Schema({}))

    async def async_step_retry(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Erneut nach CCUs suchen."""
        return await self.async_step_user({CONF_PREFIX: self._prefix})

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
                        data={CONF_CCU_ID: other, CONF_PREFIX: self._prefix, CONF_IP: ""},
                    )
                )
            return await self.async_step_ccu(
                {CONF_CCU_ID: ids[0], CONF_PREFIX: self._prefix, CONF_IP: ""}
            )
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
            elif ccu_id not in await async_collect(self.hass, self._prefix, ccu_id):
                errors["base"] = "not_found"
            else:
                return await self.async_step_ccu(
                    {CONF_CCU_ID: ccu_id, CONF_PREFIX: self._prefix, CONF_IP: ip}
                )
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
    """Nachträglich: IP des HTTP-Endpunkts ändern, alte Entities aufräumen."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
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
            step_id="init",
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
