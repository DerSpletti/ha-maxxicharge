"""Zahlen-Einstellungen mit Prüfung der Rückmeldung."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATALOG
from .coordinator import MaxxiCoordinator, num_matches
from .entity import MaxxiEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c: MaxxiCoordinator = entry.runtime_data
    async_add_entities(
        MaxxiNumber(c, name, CATALOG[name])
        for name, spec in c.specs.items()
        if spec.component == "number" and name in CATALOG and CATALOG[name].platform == "number"
    )


class MaxxiNumber(MaxxiEntity, NumberEntity):
    """Schreibbare Einstellung: senden, auf Bestätigung warten, sonst Fehler im UI."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: MaxxiCoordinator, name: str, item) -> None:
        super().__init__(coordinator, item.key, item.group, (name,), translation_key=item.key)
        spec = coordinator.specs[name]
        self._name = name
        self._step = spec.step or 1.0
        self._attr_native_unit_of_measurement = spec.unit
        if spec.min is not None:
            self._attr_native_min_value = spec.min
        if spec.max is not None:
            self._attr_native_max_value = spec.max
        self._attr_native_step = self._step

    @property
    def native_value(self) -> float | None:
        return self.coordinator.num(self._name)

    async def async_set_native_value(self, value: float) -> None:
        sent = int(value) if float(value).is_integer() else value
        await self.coordinator.async_write(
            self._name, sent, num_matches(float(value), max(self._step, 0.01) / 2)
        )
