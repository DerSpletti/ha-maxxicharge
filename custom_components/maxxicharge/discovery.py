"""Liest die retained MQTT-Autodiscovery-Configs der CCUs und macht daraus Specs."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import json
import logging
import re
import time
from typing import Any

from homeassistant.core import callback

from .const import DISCOVERY_QUIET, DISCOVERY_TIMEOUT

_LOGGER = logging.getLogger(__name__)

CCU_ID_RE = re.compile(r"CCU2-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}", re.IGNORECASE)
SUPPORTED = {"sensor", "binary_sensor", "number", "select", "switch"}

ABBR = {
    "avty_t": "availability_topic", "avty_tpl": "availability_template",
    "avty": "availability", "cmd_t": "command_topic", "cmd_tpl": "command_template",
    "stat_t": "state_topic", "val_tpl": "value_template", "uniq_id": "unique_id",
    "dev_cla": "device_class", "unit_of_meas": "unit_of_measurement",
    "stat_cla": "state_class", "ent_cat": "entity_category",
    "pl_on": "payload_on", "pl_off": "payload_off", "stat_on": "state_on",
    "stat_off": "state_off", "pl_avail": "payload_available",
    "pl_not_avail": "payload_not_available", "ops": "options", "dev": "device", "p": "platform",
}
DEV_ABBR = {
    "ids": "identifiers", "mf": "manufacturer", "mdl": "model",
    "sw": "sw_version", "cns": "connections",
}
TOPIC_KEYS = ("availability_topic", "command_topic", "state_topic")


@dataclass(slots=True)
class Spec:
    """Eine von der CCU per Discovery angemeldete Entity (nur was wir brauchen)."""

    component: str
    name: str
    ccu_id: str
    unique_id: str | None = None
    state_topic: str | None = None
    command_topic: str | None = None
    value_template: str | None = None
    command_template: str | None = None
    availability_topic: str | None = None
    payload_available: str = "online"
    payload_not_available: str = "offline"
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    options: list[str] = field(default_factory=list)
    payload_on: str = "ON"
    payload_off: str = "OFF"
    state_on: str = "ON"
    state_off: str = "OFF"
    model: str | None = None


def _expand(cfg: dict[str, Any]) -> dict[str, Any]:
    out = {ABBR.get(k, k): v for k, v in cfg.items()}
    dev = out.get("device")
    if isinstance(dev, dict):
        out["device"] = {DEV_ABBR.get(k, k): v for k, v in dev.items()}
    base = out.get("~")
    if isinstance(base, str):
        for key in TOPIC_KEYS:
            val = out.get(key)
            if isinstance(val, str):
                if val.startswith("~"):
                    out[key] = base + val[1:]
                elif val.endswith("~"):
                    out[key] = val[:-1] + base
    return out


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _find_ccu_id(cfg: dict[str, Any]) -> str | None:
    dev = cfg.get("device") if isinstance(cfg.get("device"), dict) else {}
    text = json.dumps([cfg.get("unique_id"), dev.get("identifiers"), dev.get("name")])
    match = CCU_ID_RE.search(text)
    return match.group(0).upper() if match else None


def _spec_from(component: str, cfg: dict[str, Any]) -> Spec | None:
    """Spec aus einer bereits expandierten Einzel-Config (inkl. 'device')."""
    ccu_id = _find_ccu_id(cfg)
    name = cfg.get("name")
    if component not in SUPPORTED or not ccu_id or not isinstance(name, str):
        return None

    avail_topic = cfg.get("availability_topic")
    pl_av, pl_nav = cfg.get("payload_available"), cfg.get("payload_not_available")
    avail = cfg.get("availability")
    if not avail_topic and isinstance(avail, list) and avail and isinstance(avail[0], dict):
        first = {ABBR.get(k, k): v for k, v in avail[0].items()}
        avail_topic = first.get("topic") or first.get("t")
        pl_av = first.get("payload_available", pl_av)
        pl_nav = first.get("payload_not_available", pl_nav)

    dev = cfg.get("device") if isinstance(cfg.get("device"), dict) else {}
    payload_on = str(cfg.get("payload_on", "ON"))
    payload_off = str(cfg.get("payload_off", "OFF"))
    options = cfg.get("options")
    return Spec(
        component=component,
        name=name,
        ccu_id=ccu_id,
        unique_id=cfg.get("unique_id"),
        state_topic=cfg.get("state_topic"),
        command_topic=cfg.get("command_topic"),
        value_template=cfg.get("value_template"),
        command_template=cfg.get("command_template"),
        availability_topic=avail_topic,
        payload_available=str(pl_av if pl_av is not None else "online"),
        payload_not_available=str(pl_nav if pl_nav is not None else "offline"),
        unit=cfg.get("unit_of_measurement"),
        device_class=cfg.get("device_class"),
        state_class=cfg.get("state_class"),
        min=_num(cfg.get("min")),
        max=_num(cfg.get("max")),
        step=_num(cfg.get("step")),
        options=[str(o) for o in options] if isinstance(options, list) else [],
        payload_on=payload_on,
        payload_off=payload_off,
        state_on=str(cfg.get("state_on", payload_on)),
        state_off=str(cfg.get("state_off", payload_off)),
        model=dev.get("model"),
    )


def parse_message(prefix: str, topic: str, payload: str) -> list[Spec]:
    """Eine Discovery-Nachricht lesen: Einzel-Entity oder Geräte-Discovery (mit 'cmps')."""
    if not payload or not topic.startswith(prefix + "/"):
        return []
    component = topic[len(prefix) + 1 :].split("/")[0]
    try:
        raw = json.loads(payload)
    except ValueError:
        return []
    if not isinstance(raw, dict):
        return []
    if component != "device" and "cmps" not in raw and "components" not in raw:
        spec = _spec_from(component, _expand(raw))
        return [spec] if spec else []

    # Geräte-Discovery: gemeinsame Felder oben, Entities unter "cmps"/"components"
    cmps = raw.get("cmps") or raw.get("components")
    if not isinstance(cmps, dict):
        return []
    dev_raw = raw.get("dev") or raw.get("device")
    shared = {k: v for k, v in raw.items() if k not in ("cmps", "components", "dev", "device", "o", "origin")}
    out: list[Spec] = []
    for key, comp in cmps.items():
        if not isinstance(comp, dict):
            continue
        comp_raw = {("platform" if k == "p" else k): v for k, v in comp.items()}
        merged = {**shared, **comp_raw, "device": dev_raw}
        merged.setdefault("name", key)
        if "unique_id" not in merged and "uniq_id" not in merged:
            merged["unique_id"] = f"{key}"
        cfg = _expand(merged)
        spec = _spec_from(str(cfg.get("platform") or ""), cfg)
        if spec:
            out.append(spec)
    return out


def parse_config(prefix: str, topic: str, payload: str) -> Spec | None:
    """Einzel-Entity (Kompatibilität)."""
    specs = parse_message(prefix, topic, payload)
    return specs[0] if specs else None


def specs_to_json(specs: dict[str, Spec]) -> dict[str, Any]:
    return {name: asdict(spec) for name, spec in specs.items()}


def specs_from_json(data: dict[str, Any]) -> dict[str, Spec]:
    out: dict[str, Spec] = {}
    for name, d in data.items():
        try:
            out[name] = Spec(**d)
        except TypeError:  # Cache aus anderer Version
            return {}
    return out


async def async_collect(
    bus: Any, prefix: str, ccu_id: str | None = None, timeout: float = DISCOVERY_TIMEOUT
) -> dict[str, dict[str, Spec]]:
    """Discovery-Configs einsammeln: {ccu_id: {entity_name: Spec}}."""
    found: dict[str, dict[str, Spec]] = {}
    last = time.monotonic()

    seen: list[str] = []

    @callback
    def _on_msg(msg: Any) -> None:
        nonlocal last
        try:
            specs = parse_message(prefix, msg.topic, msg.payload)
        except Exception:  # noqa: BLE001 - nie den Event-Loop stören
            _LOGGER.debug("Discovery-Nachricht %s nicht lesbar", msg.topic, exc_info=True)
            return
        if not specs:
            if len(seen) < 5 and msg.topic not in seen:
                seen.append(msg.topic)
            return
        for spec in specs:
            if ccu_id and spec.ccu_id != ccu_id:
                continue
            found.setdefault(spec.ccu_id, {})[spec.name] = spec
            last = time.monotonic()

    unsubs = [
        await bus.subscribe(f"{prefix}/+/+/config", _on_msg),
        await bus.subscribe(f"{prefix}/+/+/+/config", _on_msg),
    ]
    try:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            await asyncio.sleep(0.25)
            if found and time.monotonic() - last >= DISCOVERY_QUIET:
                break
    finally:
        for unsub in unsubs:
            unsub()
    if not found and seen:
        _LOGGER.warning(
            "Discovery-Nachrichten empfangen, aber keine CCU erkannt (Topics, Beispiele): %s", ", ".join(seen)
        )
    return found
