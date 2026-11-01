"""Gesamtübersicht über alle CCUs und Schreibschutz."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from . import calc
from .const import (
    CONF_KIND,
    DOMAIN,
    KIND_CCU,
    TOTAL_TICK,
)
from .coordinator import MaxxiCoordinator, capacity_kwh, to_kwh

_LOGGER = logging.getLogger(__name__)
FAULTS = ("Inverter Fault", "Battery Fault", "Meter Timeout")


class TotalCoordinator:
    """Rechnet über alle geladenen CCUs und hält den Schreibschutz."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.data: dict[str, Any] = {}
        self.write_lock = False
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []

    # ---------- Lebenszyklus ----------
    async def async_start(self) -> None:
        self.compute()
        self._unsubs.append(
            async_track_time_interval(self.hass, self._tick, timedelta(seconds=TOTAL_TICK))
        )

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self.hass.data.get(DOMAIN, {}).pop("write_lock", None)

    @callback
    def async_add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(cb)

        @callback
        def _remove() -> None:
            if cb in self._listeners:
                self._listeners.remove(cb)

        return _remove

    @callback
    def notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Fehler beim Aktualisieren einer Gesamt-Entity")

    @callback
    def _tick(self, _now: datetime) -> None:
        self.compute()
        self.notify()

    # ---------- Schreibschutz ----------
    @callback
    def set_write_lock(self, value: bool) -> None:
        self.write_lock = value
        store = self.hass.data.setdefault(DOMAIN, {})
        if value:
            store["write_lock"] = True
        else:
            store.pop("write_lock", None)
        self.notify()

    # ---------- CCUs ----------
    def all_ccus(self) -> list[MaxxiCoordinator]:
        out = []
        for e in self.hass.config_entries.async_entries(DOMAIN):
            if e.data.get(CONF_KIND, KIND_CCU) == KIND_CCU and e.state is ConfigEntryState.LOADED:
                if isinstance(getattr(e, "runtime_data", None), MaxxiCoordinator):
                    out.append(e.runtime_data)
        return out

    def _avail(self) -> list[MaxxiCoordinator]:
        return [c for c in self.all_ccus() if c.available]

    # ---------- Berechnung ----------
    def compute(self) -> None:
        cs = self._avail()

        def vals(name: str) -> list[float]:
            return [v for c in cs if (v := c.num(name)) is not None]

        def total(name: str) -> float | None:
            v = vals(name)
            return round(sum(v), 1) if v else None

        def mean(name: str) -> float | None:
            v = vals(name)
            return round(sum(v) / len(v), 1) if v else None

        def kwh_vals(name: str) -> list[float]:
            return [k for c in cs if (k := to_kwh(c.num(name), c.unit(name))) is not None]

        def kwh_sum(name: str) -> float | None:
            v = kwh_vals(name)
            return round(sum(v), 3) if v else None

        def kwh_mean(name: str) -> float | None:
            v = kwh_vals(name)
            return round(sum(v) / len(v), 3) if v else None

        remaining = kwh_sum("Usable Energy Remaining")
        caps = [k for c in cs if (k := capacity_kwh(c)) is not None]
        capacity = round(sum(caps), 3) if caps else None
        charge, discharge = total("Battery Charging Power"), total("Battery Discharging Power")
        ac = vals("CCU AC Power")
        feed = round(sum(max(v, 0.0) for v in ac), 1) if ac else None
        draw = round(sum(max(-v, 0.0) for v in ac), 1) if ac else None
        grid = mean("Grid Power")  # alle CCUs hängen am selben Zähler
        import_today, export_today = kwh_mean("Grid Import Energy Today"), kwh_mean("Grid Export Energy Today")
        house_today = calc.house_energy_today(
            import_today, export_today, kwh_sum("CCU AC Output Energy Today"), kwh_sum("CCU AC Input Energy Today")
        )
        pv_today = kwh_sum("PV Energy Today")
        all_c = self.all_ccus()
        self.data = {
            "total_soc": calc.weighted_soc(remaining, capacity),
            "total_usable_energy": remaining,
            "total_capacity": capacity,
            "total_battery_charge_power": charge,
            "total_battery_discharge_power": discharge,
            "total_pv_power": total("PV Power"),
            "total_grid_power": grid,
            "total_house_power": calc.house_power(grid, feed, draw),
            "total_ac_feed": feed,
            "total_ac_draw": draw,
            "total_temperature": max(vals("CCU Temperature"), default=None),
            "total_pv_today": pv_today,
            "total_house_today": house_today,
            "total_autarky": calc.autarky(import_today, house_today),
            "total_self_consumption": calc.self_consumption(export_today, pv_today),
            "total_runtime": calc.hours_left(remaining, discharge),
            "total_time_to_full": calc.hours_left(
                None if capacity is None or remaining is None else max(capacity - remaining, 0.0), charge
            ),
            "total_online": bool(all_c) and len(cs) == len(all_c),
            "total_fault": any(self._is_on(c, n) for c in cs for n in FAULTS),
        }

    @staticmethod
    def _is_on(c: MaxxiCoordinator, name: str) -> bool:
        spec, val = c.specs.get(name), c.value(name)
        return bool(spec and val and val.lower() == spec.state_on.lower())
