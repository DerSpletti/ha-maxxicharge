"""Auswahl-Einstellungen (Ladestrategie) mit Prüfung."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATALOG, DOMAIN, SELECT_LABELS_DE
from .coordinator import MaxxiCoordinator
from .entity import MaxxiEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c: MaxxiCoordinator = entry.runtime_data
    german = hass.config.language.startswith("de")
    async_add_entities(
        MaxxiSelect(c, name, CATALOG[name], german)
        for name, spec in c.specs.items()
        if spec.component == "select" and name in CATALOG and CATALOG[name].platform == "select"
    )


class MaxxiSelect(MaxxiEntity, SelectEntity):
    """Schreibbare Auswahl: Anzeige ggf. deutsch, gesendet wird der Originalwert."""

    def __init__(self, coordinator: MaxxiCoordinator, name: str, item, german: bool) -> None:
        super().__init__(coordinator, item.key, item.group, (name,), translation_key=item.key)
        self._name = name
        raw = coordinator.specs[name].options
        self._to_label = {o: (SELECT_LABELS_DE.get(o, o) if german else o) for o in raw}
        self._to_raw = {v: k for k, v in self._to_label.items()}
        self._attr_options = list(self._to_label.values())

    @property
    def current_option(self) -> str | None:
        return self._to_label.get(self.coordinator.value(self._name) or "")

    async def async_select_option(self, option: str) -> None:
        raw = self._to_raw.get(option)
        if raw is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="invalid_option",
                translation_placeholders={"option": option},
            )
        await self.coordinator.async_write(self._name, raw, lambda v: v == raw)
