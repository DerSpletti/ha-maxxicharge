"""Hintergrund-Erkennung: meldet sich eine unbekannte CCU, erscheint sie unter „Entdeckt“."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY, ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_USER,
    CONF_CCU_ID,
    CONF_IP,
    CONF_MODE,
    CONF_PREFIX,
    DOMAIN,
)
from .discovery import parse_message

_LOGGER = logging.getLogger(__name__)
_COPY = (CONF_MODE, CONF_PREFIX, CONF_BROKER_PORT, CONF_BROKER_USER, CONF_BROKER_PASSWORD)


async def async_start_watcher(
    hass: HomeAssistant, entry: ConfigEntry, bus: Any, prefix: str
) -> Callable[[], None]:
    """Auf Discovery-Meldungen lauschen; neue CCUs als Entdeckung anbieten."""
    known: set[str] = set()

    @callback
    def _on_msg(msg: Any) -> None:
        try:
            specs = parse_message(prefix, msg.topic, msg.payload)
        except Exception:  # noqa: BLE001
            return
        for spec in specs:
            ccu_id = spec.ccu_id
            if ccu_id in known:
                continue
            known.add(ccu_id)
            if any(e.data.get(CONF_CCU_ID) == ccu_id for e in hass.config_entries.async_entries(DOMAIN)):
                continue
            data = {k: entry.data[k] for k in _COPY if k in entry.data}
            data.update({CONF_CCU_ID: ccu_id, CONF_IP: ""})
            _LOGGER.info("Neue CCU %s entdeckt", ccu_id)
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_INTEGRATION_DISCOVERY}, data=data
                )
            )

    unsubs = [
        await bus.subscribe(f"{prefix}/+/+/config", _on_msg),
        await bus.subscribe(f"{prefix}/+/+/+/config", _on_msg),
    ]

    @callback
    def _stop() -> None:
        for unsub in unsubs:
            unsub()

    return _stop
