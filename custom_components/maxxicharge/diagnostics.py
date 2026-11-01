"""Diagnose-Download (Zugangsdaten gibt es nicht, IP/ID werden geschwärzt)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CCU_ID, CONF_IP, CONF_KIND, KIND_TOTAL

TO_REDACT = {CONF_CCU_ID, CONF_IP, "broker_password", "broker_user", "unique_id", "CCU IP", "CCU ID", "serial_number"}


def _mask(text: str | None, ccu_id: str) -> str | None:
    """CCU-ID (Seriennummer) in Topics durch einen Platzhalter ersetzen."""
    return text.replace(ccu_id, "CCU2-XXXX-XXXX-XXXX") if text else text


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    c = entry.runtime_data
    if entry.data.get(CONF_KIND) == KIND_TOTAL:
        return {
            "kind": "total",
            "options": dict(entry.options),
            "values": dict(c.data),
            "write_lock": c.write_lock,
        }
    broker = getattr(c.bus, "broker", None)
    stat = broker.client_stat(c.ccu_id) if broker else None
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "model": c.model,
        "model_reported": c.model_raw,
        "source": c.source,
        "topics_subscribed": c.topic_count,
        "broker_client": (
            {k: stat.get(k) for k in ("connected", "since", "last_publish", "closed", "closed_at")} if stat else None
        ),
        "firmware": c.firmware,
        "writable": c.writable,
        "available": c.available,
        "online_flag": c.online,
        "last_update": c.last_update.isoformat() if c.last_update else None,
        "values": async_redact_data(dict(c.values), TO_REDACT),
        "entities": {
            name: {
                "component": s.component,
                "state_topic": _mask(s.state_topic, c.ccu_id),
                "command_topic": _mask(s.command_topic, c.ccu_id),
                "template": s.value_template,
                "unit": s.unit,
                "options": s.options,
                "min": s.min,
                "max": s.max,
                "step": s.step,
            }
            for name, s in c.specs.items()
        },
    }
