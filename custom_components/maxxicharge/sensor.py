"""Sensoren: aufgeräumte CCU-Werte plus abgeleitete Werte."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    DEVICE_CLASS_UNITS,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from . import calc
from .const import CATALOG, CONF_KIND, DERIVED, G_DIAG_OFF, KIND_CCU, KIND_TOTAL, OPERATING_MODES_DE, TICK
from .coordinator import MaxxiCoordinator, capacity_kwh, to_kwh
from .entity import MaxxiEntity

_BAD_CLASSES = {SensorDeviceClass.TIMESTAMP, SensorDeviceClass.DATE, SensorDeviceClass.ENUM}
_ITEMS = {i.key: i for i in DERIVED}


def _device_class(device_class: str | None, unit: str | None) -> SensorDeviceClass | None:
    if not device_class:
        return None
    try:
        dc = SensorDeviceClass(device_class)
    except ValueError:
        return None
    if dc in _BAD_CLASSES:
        return None
    allowed = DEVICE_CLASS_UNITS.get(dc)
    if allowed is not None and unit not in allowed:
        return None
    return dc


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry.data.get(CONF_KIND, KIND_CCU) == KIND_TOTAL:
        from .total_entities import SENSORS, TotalSensor

        async_add_entities([TotalSensor(entry.runtime_data, key) for key in SENSORS])
        return
    c: MaxxiCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for name, spec in c.specs.items():
        if spec.component != "sensor":
            continue
        item = CATALOG.get(name)
        if item is not None and item.platform != "sensor":
            continue
        entities.append(MaxxiSensor(c, name, item))

    def derived(key: str, sources: tuple[str, ...], fn: Callable[[MaxxiCoordinator], Any], **kw: Any) -> None:
        if all(s in c.specs for s in sources):
            entities.append(MaxxiDerivedSensor(c, _ITEMS[key], sources, fn, **kw))

    ac = "CCU AC Power"
    derived("ac_feed_power", (ac,), lambda c: None if c.num(ac) is None else max(c.num(ac), 0.0),
            unit=lambda c: c.unit(ac) or "W", dc=SensorDeviceClass.POWER, sc=SensorStateClass.MEASUREMENT)
    derived("ac_draw_power", (ac,), lambda c: None if c.num(ac) is None else max(-c.num(ac), 0.0) + 0.0,
            unit=lambda c: c.unit(ac) or "W", dc=SensorDeviceClass.POWER, sc=SensorStateClass.MEASUREMENT)
    rem = "Usable Energy Remaining"
    derived("usable_energy_kwh", (rem,), lambda c: to_kwh(c.num(rem), c.unit(rem)),
            unit=lambda c: "kWh", dc=SensorDeviceClass.ENERGY_STORAGE, sc=SensorStateClass.MEASUREMENT, digits=2)
    gi, ge = "Grid Import Energy Total", "Grid Export Energy Total"
    derived("grid_balance", (gi, ge),
            lambda c: None if None in (to_kwh(c.num(gi), c.unit(gi)), to_kwh(c.num(ge), c.unit(ge)))
            else to_kwh(c.num(gi), c.unit(gi)) - to_kwh(c.num(ge), c.unit(ge)),
            unit=lambda c: "kWh", dc=SensorDeviceClass.ENERGY, sc=SensorStateClass.TOTAL, digits=2)
    bd, bc = "Battery Discharging Energy", "Battery Charging Energy"
    derived("battery_balance", (bd, bc),
            lambda c: None if None in (to_kwh(c.num(bd), c.unit(bd)), to_kwh(c.num(bc), c.unit(bc)))
            else to_kwh(c.num(bd), c.unit(bd)) - to_kwh(c.num(bc), c.unit(bc)),
            unit=lambda c: "kWh", dc=SensorDeviceClass.ENERGY, sc=SensorStateClass.TOTAL, digits=2)
    rem_n, dp_n, cp_n = "Usable Energy Remaining", "Battery Discharging Power", "Battery Charging Power"
    derived("efficiency", (bd, bc),
            lambda c: calc.efficiency(to_kwh(c.num(bd), c.unit(bd)), to_kwh(c.num(bc), c.unit(bc))),
            unit=lambda c: "%", dc=None, sc=SensorStateClass.MEASUREMENT, digits=1)
    derived("cycles", (bd,),
            lambda c: calc.cycles(to_kwh(c.num(bd), c.unit(bd)), capacity_kwh(c)),
            unit=lambda c: None, dc=None, sc=SensorStateClass.TOTAL_INCREASING, digits=1)
    derived("runtime", (rem_n, dp_n),
            lambda c: calc.hours_left(to_kwh(c.num(rem_n), c.unit(rem_n)), c.num(dp_n)),
            unit=lambda c: "h", dc=SensorDeviceClass.DURATION, sc=SensorStateClass.MEASUREMENT, digits=1)

    def _to_full(c: MaxxiCoordinator) -> float | None:
        cap, rem = capacity_kwh(c), to_kwh(c.num(rem_n), c.unit(rem_n))
        if cap is None or rem is None:
            return None
        return calc.hours_left(max(cap - rem, 0.0), c.num(cp_n))

    derived("time_to_full", (rem_n, cp_n), _to_full,
            unit=lambda c: "h", dc=SensorDeviceClass.DURATION, sc=SensorStateClass.MEASUREMENT, digits=1)
    entities.append(MaxxiLastUpdateSensor(c, _ITEMS["last_update"]))
    async_add_entities(entities)


class MaxxiSensor(MaxxiEntity, SensorEntity):
    """Wert direkt aus der CCU."""

    def __init__(self, coordinator: MaxxiCoordinator, name: str, item: Any) -> None:
        spec = coordinator.specs[name]
        self._name = name
        if item is not None:
            super().__init__(coordinator, item.key, item.group, (name,), translation_key=item.key)
        else:  # unbekannt: nichts verlieren, aber deaktiviert
            super().__init__(coordinator, f"x_{slugify(name)}", G_DIAG_OFF, (name,), name=name)
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_device_class = _device_class(spec.device_class, spec.unit)
        try:
            self._attr_state_class = SensorStateClass(spec.state_class) if spec.state_class else None
        except ValueError:
            self._attr_state_class = None
        self._numeric = bool(spec.unit or self._attr_device_class or self._attr_state_class)

    @property
    def native_value(self) -> float | str | None:
        val = self.coordinator.value(self._name)
        if val is not None and self._name == "Operating Mode" and self.hass.config.language.startswith("de"):
            return OPERATING_MODES_DE.get(val.strip().lower(), val)  # unbekannte Werte unverändert
        if val is None or not self._numeric:
            return val
        try:
            return float(val)
        except ValueError:
            return None


class MaxxiDerivedSensor(MaxxiEntity, SensorEntity):
    """Berechneter Wert."""

    def __init__(
        self,
        coordinator: MaxxiCoordinator,
        item: Any,
        sources: tuple[str, ...],
        fn: Callable[[MaxxiCoordinator], Any],
        unit: Callable[[MaxxiCoordinator], str],
        dc: SensorDeviceClass,
        sc: SensorStateClass,
        digits: int | None = None,
    ) -> None:
        super().__init__(coordinator, item.key, item.group, sources, translation_key=item.key)
        self._fn = fn
        self._attr_native_unit_of_measurement = unit(coordinator)
        self._attr_device_class = dc
        self._attr_state_class = sc
        if digits is not None:
            self._attr_suggested_display_precision = digits

    @property
    def native_value(self) -> float | None:
        return self._fn(self.coordinator)


class MaxxiLastUpdateSensor(MaxxiEntity, SensorEntity):
    """Zeitpunkt der letzten Nachricht der CCU (bleibt auch offline sichtbar)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    always_available = True

    def __init__(self, coordinator: MaxxiCoordinator, item: Any) -> None:
        super().__init__(coordinator, item.key, item.group, (TICK,), translation_key=item.key)

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_update
