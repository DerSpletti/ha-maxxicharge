"""Push-Koordinator: hält die Werte einer CCU und schreibt Einstellungen mit Prüfung."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CCU_ID,
    CONF_IP,
    DOMAIN,
    MIN_WRITE_FIRMWARE,
    STALE_AFTER,
    TICK,
    TICK_SECONDS,
    WRITE_TIMEOUT,
)
from .discovery import Spec

_LOGGER = logging.getLogger(__name__)

_EMPTY = {"", "none", "unknown", "unavailable", "null"}
Predicate = Callable[[str | None], bool]


def num_matches(target: float, tolerance: float = 0.5) -> Predicate:
    """Erwartung für Zahlenwerte."""

    def _check(value: str | None) -> bool:
        try:
            return value is not None and abs(float(value) - target) <= tolerance
        except ValueError:
            return False

    return _check


def to_kwh(value: float | None, unit: str | None) -> float | None:
    """Energie in kWh umrechnen; ohne bekannte Einheit kein Wert (nichts raten)."""
    if value is None or unit is None:
        return None
    factor = {"wh": 0.001, "kwh": 1.0, "mwh": 1000.0}.get(unit.strip().lower())
    return None if factor is None else value * factor


class MaxxiCoordinator:
    """Eine CCU: MQTT-Push, Verfügbarkeit, Firmware und verifiziertes Schreiben."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, specs: dict[str, Spec], bus: Any) -> None:
        self.hass = hass
        self.bus = bus
        self.entry = entry
        self.ccu_id: str = entry.data[CONF_CCU_ID]
        self.specs = specs
        self.values: dict[str, str | None] = {}
        self.last_update: datetime | None = None
        self.online: bool | None = None
        self._templates: dict[str, Template] = {}
        self._by_topic: dict[str, list[str]] = {}
        self._listeners: list[tuple[frozenset[str] | None, Callable[[], None]]] = []
        self._waiters: dict[str, list[tuple[Predicate, asyncio.Future[bool]]]] = {}
        self._unsubs: list[Callable[[], None]] = []
        self._avail_topic: str | None = None
        self._pl_avail = "online"
        self._pl_not_avail = "offline"
        self._last_avail: bool | None = None
        self._warned_fw = False

        for name, spec in specs.items():
            if spec.state_topic:
                self._by_topic.setdefault(spec.state_topic, []).append(name)
                if spec.value_template:
                    self._templates[name] = Template(spec.value_template, hass)
            if spec.availability_topic and not self._avail_topic:
                self._avail_topic = spec.availability_topic
                self._pl_avail = spec.payload_available
                self._pl_not_avail = spec.payload_not_available

    # ---------- Lebenszyklus ----------
    async def async_start(self) -> None:
        for topic in self._by_topic:
            self._unsubs.append(
                await self.bus.subscribe(topic, self._handle_state)
            )
        if self._avail_topic:
            self._unsubs.append(
                await self.bus.subscribe(self._avail_topic, self._handle_availability)
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._tick, timedelta(seconds=TICK_SECONDS))
        )

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)

    # ---------- Listener ----------
    @callback
    def async_add_listener(
        self, cb: Callable[[], None], names: frozenset[str] | set[str] | None = None
    ) -> Callable[[], None]:
        item = (frozenset(names) if names is not None else None, cb)
        self._listeners.append(item)

        @callback
        def _remove() -> None:
            if item in self._listeners:
                self._listeners.remove(item)

        return _remove

    @callback
    def _notify(self, changed: set[str] | None) -> None:
        """changed=None: alle benachrichtigen."""
        for names, cb in list(self._listeners):
            if changed is None or names is None or names & changed:
                try:
                    cb()
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Fehler beim Aktualisieren einer Entity")

    # ---------- Eingehende Daten ----------
    def _render(self, name: str, payload: str) -> str | None:
        tpl = self._templates.get(name)
        val: Any = payload if tpl is None else tpl.async_render_with_possible_json_value(payload, None)
        if val is None:
            return None
        text = str(val).strip()
        return None if text.lower() in _EMPTY else text

    @callback
    def _handle_state(self, msg: Any) -> None:
        payload = msg.payload if isinstance(msg.payload, str) else msg.payload.decode(errors="replace")
        changed: set[str] = set()
        names = self._by_topic.get(msg.topic, [])
        for name in names:
            try:
                val = self._render(name, payload)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Wert für %s nicht lesbar: %s", name, payload, exc_info=True)
                continue
            if name not in self.values or self.values[name] != val:
                self.values[name] = val
                changed.add(name)
        self.last_update = dt_util.utcnow()
        for name in names:
            for expect, fut in list(self._waiters.get(name, [])):
                if not fut.done() and expect(self.values.get(name)):
                    fut.set_result(True)
        if "CCU ver" in changed:
            self._check_firmware()
        self._notify(changed)
        self._notify_availability()

    @callback
    def _handle_availability(self, msg: Any) -> None:
        payload = msg.payload if isinstance(msg.payload, str) else msg.payload.decode(errors="replace")
        if payload == self._pl_avail:
            self.online = True
        elif payload == self._pl_not_avail:
            self.online = False
        self._notify_availability()

    @callback
    def _notify_availability(self) -> None:
        now = self.available
        if now != self._last_avail:
            self._last_avail = now
            self._notify(None)

    @callback
    def _tick(self, _now: datetime) -> None:
        self._notify_availability()
        self._notify({TICK})

    # ---------- Zustand ----------
    @property
    def available(self) -> bool:
        if self.online is False or self.last_update is None:
            return False
        return (dt_util.utcnow() - self.last_update).total_seconds() < STALE_AFTER

    def value(self, name: str) -> str | None:
        return self.values.get(name)

    def num(self, name: str) -> float | None:
        try:
            val = self.values.get(name)
            return None if val is None else float(val)
        except ValueError:
            return None

    def unit(self, name: str) -> str | None:
        spec = self.specs.get(name)
        return spec.unit if spec else None

    @property
    def firmware(self) -> str | None:
        return self.values.get("CCU ver")

    @property
    def firmware_tuple(self) -> tuple[int, ...] | None:
        fw = self.firmware
        if not fw:
            return None
        parts = re.findall(r"\d+", fw)
        return tuple(int(p) for p in parts[:3]) if parts else None

    @property
    def writable(self) -> bool | None:
        """True/False je nach Firmware, None solange die Firmware unbekannt ist."""
        fw = self.firmware_tuple
        return None if fw is None else fw >= MIN_WRITE_FIRMWARE

    @property
    def ip(self) -> str | None:
        return self.entry.options.get(CONF_IP) or self.entry.data.get(CONF_IP) or self.value("CCU IP")

    @property
    def device_info(self) -> DeviceInfo:
        model = next((s.model for s in self.specs.values() if s.model), None)
        return DeviceInfo(
            identifiers={(DOMAIN, self.ccu_id)},
            name=f"CCU {self.ccu_id[-4:]}",
            manufacturer="Maxxisun",
            model=model or "CCU Gen2",
            serial_number=self.ccu_id,
            sw_version=self.firmware,
            configuration_url=f"http://{self.ip}" if self.ip else None,
        )

    # ---------- Firmware-Hinweis ----------
    @property
    def _issue_id(self) -> str:
        return f"firmware_{self.ccu_id}"

    @callback
    def _check_firmware(self) -> None:
        if self.writable is False:
            if not self._warned_fw:
                _LOGGER.warning(
                    "CCU %s hat Firmware %s: Einstellungen schreiben ist erst ab 2.43 möglich",
                    self.ccu_id,
                    self.firmware,
                )
                self._warned_fw = True
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self._issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="firmware_too_old",
                translation_placeholders={"ccu": self.ccu_id, "version": self.firmware or "?"},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)

    # ---------- Schreiben mit Prüfung ----------
    def format_command(self, spec: Spec, value: Any) -> str:
        if spec.command_template:
            return str(
                Template(spec.command_template, self.hass).async_render(
                    {"value": value}, parse_result=False
                )
            )
        return str(value)

    async def async_write(self, name: str, value: Any, expect: Predicate) -> None:
        """Wert senden und auf Bestätigung warten; sonst HomeAssistantError."""
        spec = self.specs.get(name)
        err = {"name": name, "value": str(value), "current": str(self.values.get(name)), "version": self.firmware or "?"}
        if spec is None or not spec.command_topic:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="no_command_topic", translation_placeholders=err)
        if self.writable is False:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="firmware_too_old_write", translation_placeholders=err)
        if not self.available:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="ccu_offline", translation_placeholders=err)
        if expect(self.values.get(name)):
            return  # Zustand ist schon so

        payload = self.format_command(spec, value)
        fut: asyncio.Future[bool] = self.hass.loop.create_future()
        waiter = (expect, fut)
        self._waiters.setdefault(name, []).append(waiter)
        try:
            _LOGGER.debug("Schreibe %s=%s auf %s", name, payload, spec.command_topic)
            try:
                await self.bus.publish(spec.command_topic, payload, False)
            except HomeAssistantError as exc:
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="publish_failed", translation_placeholders=err) from exc
            try:
                async with asyncio.timeout(WRITE_TIMEOUT):
                    await fut
            except TimeoutError as exc:
                err["current"] = str(self.values.get(name))
                _LOGGER.warning(
                    "CCU %s hat %s=%s nicht übernommen (aktuell: %s, nach %.0f s)",
                    self.ccu_id, name, payload, err["current"], WRITE_TIMEOUT,
                )
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="write_failed", translation_placeholders=err) from exc
            _LOGGER.debug("CCU %s hat %s=%s bestätigt", self.ccu_id, name, payload)
        finally:
            if waiter in self._waiters.get(name, []):
                self._waiters[name].remove(waiter)
            if not fut.done():
                fut.cancel()
            self._notify({name})  # Entity zeigt wieder den echten Wert
