"""Gemeinsame Basisklasse."""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .const import G_CONFIG, G_DIAG, G_DIAG_OFF
from .coordinator import MaxxiCoordinator

CATEGORY = {
    G_CONFIG: EntityCategory.CONFIG,
    G_DIAG: EntityCategory.DIAGNOSTIC,
    G_DIAG_OFF: EntityCategory.DIAGNOSTIC,
}


class MaxxiEntity(Entity):
    """Basis: hängt am Koordinator, schreibt den Zustand bei Änderung der Quellwerte."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    always_available = False

    def __init__(
        self,
        coordinator: MaxxiCoordinator,
        unique_key: str,
        group: str,
        sources: Iterable[str],
        translation_key: str | None = None,
        name: str | None = None,
    ) -> None:
        self.coordinator = coordinator
        self._sources = frozenset(sources)
        self._attr_unique_id = f"{coordinator.ccu_id}_{unique_key}"
        self._attr_translation_key = translation_key
        if translation_key is None:
            self._attr_name = name
        self._attr_entity_category = CATEGORY.get(group)
        self._attr_entity_registry_enabled_default = group != G_DIAG_OFF
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        return True if self.always_available else self.coordinator.available

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._on_update, self._sources))

    @callback
    def _on_update(self) -> None:
        self.async_write_ha_state()
