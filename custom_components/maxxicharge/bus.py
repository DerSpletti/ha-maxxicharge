"""Nachrichtenweg: entweder die MQTT-Integration von Home Assistant oder der eingebaute Broker."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback

from .broker import MiniBroker
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STOP_GRACE = 30  # Sekunden, bevor ein unbenutzter Broker gestoppt wird


class HaBus:
    """MQTT der Home-Assistant-Installation."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def subscribe(self, topic: str, cb: Callable[[Any], None]) -> CALLBACK_TYPE:
        return await mqtt.async_subscribe(self.hass, topic, cb, 0, "utf-8")

    async def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        await mqtt.async_publish(self.hass, topic, payload, 0, retain)


class EmbeddedBus:
    """Eingebauter Broker (kein MQTT in Home Assistant nötig)."""

    def __init__(self, broker: MiniBroker) -> None:
        self.broker = broker

    async def subscribe(self, topic: str, cb: Callable[[Any], None]) -> CALLBACK_TYPE:
        return self.broker.subscribe(topic, cb)

    async def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        self.broker.publish(topic, payload, retain)


class BrokerConflict(Exception):
    """Es läuft schon ein eingebauter Broker mit anderen Einstellungen."""


class BrokerManager:
    """Ein gemeinsamer Broker für alle CCUs und laufende Einrichtungsassistenten."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.broker: MiniBroker | None = None
        self._owners: set[str] = set()
        self._lock = asyncio.Lock()
        self._stop_handle: asyncio.TimerHandle | None = None
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_stop)

    async def acquire(self, owner: str, port: int, username: str, password: str) -> MiniBroker:
        """Broker starten (oder mitbenutzen). OSError, wenn der Port belegt ist."""
        async with self._lock:
            if self._stop_handle:
                self._stop_handle.cancel()
                self._stop_handle = None
            b = self.broker
            if b and (b.port, b.username, b.password) != (port, username, password):
                if self._owners - {owner}:
                    raise BrokerConflict
                await b.async_stop()
                self.broker = b = None
            if b is None:
                b = MiniBroker(port, username, password)
                await b.async_start()
                self.broker = b
            self._owners.add(owner)
            return b

    @callback
    def release(self, owner: str) -> None:
        self._owners.discard(owner)
        if not self._owners and self.broker and not self._stop_handle:
            self._stop_handle = self.hass.loop.call_later(
                STOP_GRACE, lambda: self.hass.async_create_task(self._stop_if_unused())
            )

    async def _stop_if_unused(self) -> None:
        async with self._lock:
            self._stop_handle = None
            if not self._owners and self.broker:
                await self.broker.async_stop()
                self.broker = None

    async def _on_stop(self, _event: Event) -> None:
        if self.broker:
            await self.broker.async_stop()
            self.broker = None


def get_manager(hass: HomeAssistant) -> BrokerManager:
    store = hass.data.setdefault(DOMAIN, {})
    if "manager" not in store:
        store["manager"] = BrokerManager(hass)
    return store["manager"]
