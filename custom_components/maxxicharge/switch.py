"""Schalter-Einstellungen (USV-Modus) mit Prüfung."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATALOG, CONF_KIND, KIND_CCU, KIND_TOTAL
from .coordinator import MaxxiCoordinator
from .entity import MaxxiEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if entry.data.get(CONF_KIND, KIND_CCU) == KIND_TOTAL:
        from .total_entities import WriteLockSwitch

        async_add_entities([WriteLockSwitch(entry.runtime_data)])
        return
    c: MaxxiCoordinator = entry.runtime_data
    async_add_entities(
        MaxxiSwitch(c, name, CATALOG[name])
        for name, spec in c.specs.items()
        if spec.component == "switch" and name in CATALOG and CATALOG[name].platform == "switch"
    )


class MaxxiSwitch(MaxxiEntity, SwitchEntity):
    """Schreibbarer Schalter: Zustand ist immer der von der CCU gemeldete."""

    def __init__(self, coordinator: MaxxiCoordinator, name: str, item) -> None:
        super().__init__(coordinator, item.key, item.group, (name,), translation_key=item.key)
        self._name = name
        self._spec = coordinator.specs[name]

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.value(self._name)
        if val is None:
            return None
        if val.lower() == self._spec.state_on.lower():
            return True
        if val.lower() == self._spec.state_off.lower():
            return False
        return None

    async def _set(self, on: bool) -> None:
        target = self._spec.state_on if on else self._spec.state_off
        payload = self._spec.payload_on if on else self._spec.payload_off
        await self.coordinator.async_write(
            self._name, payload, lambda v: v is not None and v.lower() == target.lower()
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
