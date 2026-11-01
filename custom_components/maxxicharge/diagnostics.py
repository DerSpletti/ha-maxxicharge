"""Diagnose-Download (Zugangsdaten gibt es nicht, IP/ID werden geschwärzt)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CCU_ID, CONF_IP

TO_REDACT = {CONF_CCU_ID, CONF_IP, "broker_password", "broker_user", "unique_id", "CCU IP", "CCU ID", "serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    c = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "firmware": c.firmware,
        "writable": c.writable,
        "available": c.available,
        "online_flag": c.online,
        "last_update": c.last_update.isoformat() if c.last_update else None,
        "values": async_redact_data(dict(c.values), TO_REDACT),
        "entities": {
            name: {
                "component": s.component,
                "state_topic": s.state_topic,
                "command_topic": s.command_topic,
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
