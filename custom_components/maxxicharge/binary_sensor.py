"""Binäre Sensoren: Störungen, voll/leer, Verbindung, Schreibfähigkeit."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import CATALOG, CONF_KIND, DERIVED, G_DIAG_OFF, KIND_CCU, KIND_TOTAL, TICK
from .coordinator import MaxxiCoordinator
from .entity import MaxxiEntity

_ITEMS = {i.key: i for i in DERIVED}
SOC, MAX_SOC, MIN_SOC = "Local Battery SOC", "Maximum SOC", "Minimum SOC"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry.data.get(CONF_KIND, KIND_CCU) == KIND_TOTAL:
        from .total_entities import TotalBinary

        async_add_entities([TotalBinary(entry.runtime_data, "total_online"), TotalBinary(entry.runtime_data, "total_fault")])
        return
    c: MaxxiCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for name, spec in c.specs.items():
        if spec.component != "binary_sensor":
            continue
        item = CATALOG.get(name)
        if item is not None and item.platform != "binary_sensor":
            continue
        entities.append(MaxxiBinarySensor(c, name, item))

    if SOC in c.specs:
        entities.append(MaxxiDerivedBinary(
            c, _ITEMS["full"], (SOC, MAX_SOC),
            lambda c: None if c.num(SOC) is None
            else c.num(SOC) >= (c.num(MAX_SOC) if c.num(MAX_SOC) is not None else 100.0)))
        entities.append(MaxxiDerivedBinary(
            c, _ITEMS["empty"], (SOC, MIN_SOC),
            lambda c: None if c.num(SOC) is None
            else c.num(SOC) <= (c.num(MIN_SOC) if c.num(MIN_SOC) is not None else 0.0)))
    entities.append(MaxxiDerivedBinary(
        c, _ITEMS["online"], (TICK,), lambda c: c.available,
        device_class=BinarySensorDeviceClass.CONNECTIVITY, always_available=True))
    entities.append(MaxxiDerivedBinary(
        c, _ITEMS["write_possible"], ("CCU ver",), lambda c: c.writable, always_available=True))
    async_add_entities(entities)


class MaxxiBinarySensor(MaxxiEntity, BinarySensorEntity):
    """Wert direkt aus der CCU (z. B. Fehlerflags)."""

    def __init__(self, coordinator: MaxxiCoordinator, name: str, item: Any) -> None:
        spec = coordinator.specs[name]
        self._name = name
        self._on, self._off = spec.state_on.lower(), spec.state_off.lower()
        if item is not None:
            super().__init__(coordinator, item.key, item.group, (name,), translation_key=item.key)
        else:
            super().__init__(coordinator, f"x_{slugify(name)}", G_DIAG_OFF, (name,), name=name)
        if item is not None and item.group != "main":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.value(self._name)
        if val is None:
            return None
        low = val.lower()
        if low == self._on:
            return True
        if low == self._off:
            return False
        return None


class MaxxiDerivedBinary(MaxxiEntity, BinarySensorEntity):
    """Berechneter Zustand."""

    def __init__(
        self,
        coordinator: MaxxiCoordinator,
        item: Any,
        sources: tuple[str, ...],
        fn: Callable[[MaxxiCoordinator], bool | None],
        device_class: BinarySensorDeviceClass | None = None,
        always_available: bool = False,
    ) -> None:
        super().__init__(coordinator, item.key, item.group, sources, translation_key=item.key)
        self._fn = fn
        self._attr_device_class = device_class
        self.always_available = always_available

    @property
    def is_on(self) -> bool | None:
        return self._fn(self.coordinator)
