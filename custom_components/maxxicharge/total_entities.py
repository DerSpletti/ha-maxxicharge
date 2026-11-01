"""Entities der Gesamtübersicht (Gerät „Maxxicharge Gesamt“)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, TOTAL, TOTAL_UNIQUE_ID
from .total import TotalCoordinator

_ITEMS = {i.key: i for i in TOTAL}
_DC, _SC = SensorDeviceClass, SensorStateClass
# key: (Einheit, Geräteklasse, Zustandsklasse, Nachkommastellen)
SENSORS: dict[str, tuple[str, SensorDeviceClass | None, SensorStateClass | None, int | None]] = {
    "total_soc": ("%", _DC.BATTERY, _SC.MEASUREMENT, 1),
    "total_usable_energy": ("kWh", _DC.ENERGY_STORAGE, _SC.MEASUREMENT, 2),
    "total_capacity": ("kWh", _DC.ENERGY_STORAGE, _SC.MEASUREMENT, 2),
    "total_battery_charge_power": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_battery_discharge_power": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_pv_power": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_grid_power": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_house_power": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_ac_feed": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_ac_draw": ("W", _DC.POWER, _SC.MEASUREMENT, 0),
    "total_temperature": ("°C", _DC.TEMPERATURE, _SC.MEASUREMENT, 0),
    "total_pv_today": ("kWh", _DC.ENERGY, _SC.TOTAL_INCREASING, 2),
    "total_house_today": ("kWh", _DC.ENERGY, _SC.TOTAL_INCREASING, 2),
    "total_autarky": ("%", None, _SC.MEASUREMENT, 0),
    "total_self_consumption": ("%", None, _SC.MEASUREMENT, 0),
    "total_runtime": ("h", _DC.DURATION, _SC.MEASUREMENT, 1),
    "total_time_to_full": ("h", _DC.DURATION, _SC.MEASUREMENT, 1),
}


def total_device() -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, TOTAL_UNIQUE_ID)},
        name="Maxxicharge Gesamt",
        manufacturer="Maxxisun",
        model="Gesamtübersicht",
    )


class TotalEntity(Entity):
    """Basis: hört auf den Gesamt-Koordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: TotalCoordinator, key: str) -> None:
        self.coordinator = coordinator
        self.key = key
        self._attr_unique_id = f"{TOTAL_UNIQUE_ID}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = total_device()
        group = _ITEMS[key].group
        if group == "diag":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        elif group == "config":
            self._attr_entity_category = EntityCategory.CONFIG

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self._on_update))

    @callback
    def _on_update(self) -> None:
        self.async_write_ha_state()


class TotalSensor(TotalEntity, SensorEntity):
    def __init__(self, coordinator: TotalCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        unit, dc, sc, digits = SENSORS[key]
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = dc
        self._attr_state_class = sc
        if digits is not None:
            self._attr_suggested_display_precision = digits

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self.key)


class TotalBinary(TotalEntity, BinarySensorEntity):
    def __init__(self, coordinator: TotalCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._attr_device_class = (
            BinarySensorDeviceClass.CONNECTIVITY if key == "total_online" else BinarySensorDeviceClass.PROBLEM
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self.key)


class WriteLockSwitch(TotalEntity, RestoreEntity, SwitchEntity):
    """Sperrt alle Schreibzugriffe auf die CCUs."""

    _attr_icon = "mdi:lock"

    def __init__(self, coordinator: TotalCoordinator) -> None:
        super().__init__(coordinator, "write_lock")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.set_write_lock(last.state == "on")

    @property
    def is_on(self) -> bool:
        return self.coordinator.write_lock

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.set_write_lock(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_write_lock(False)
