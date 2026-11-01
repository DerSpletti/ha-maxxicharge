"""Konstanten und Entity-Katalog für Maxxicharge (reines Python, ohne HA-Importe)."""

from __future__ import annotations

from typing import NamedTuple

DOMAIN = "maxxicharge"

CONF_CCU_ID = "ccu_id"
CONF_CCUS = "ccus"
CONF_PREFIX = "discovery_prefix"
CONF_IP = "ip"
CONF_CLEANUP = "cleanup"

DEFAULT_PREFIX = "homeassistant"

CONF_KIND = "kind"  # "ccu" (Standard) oder "total" (Gesamtübersicht)
KIND_CCU = "ccu"
KIND_TOTAL = "total"
TOTAL_UNIQUE_ID = "maxxicharge_total"
TOTAL_TICK = 5  # Sekunden: Aktualisierung der Gesamtwerte
CONF_MODE = "mode"
CONF_BROKER_PORT = "broker_port"
CONF_BROKER_USER = "broker_user"
CONF_BROKER_PASSWORD = "broker_password"
MODE_HA = "ha_mqtt"  # MQTT-Integration von Home Assistant
MODE_EMBEDDED = "embedded"  # eingebauter Broker
DEFAULT_BROKER_PORT = 1883
DEFAULT_BROKER_USER = "maxxicharge"
EMBEDDED_WAIT = 60.0  # so lange wartet der eingebaute Broker beim Start auf die Discovery der CCU

MIN_WRITE_FIRMWARE = (2, 43, 0)  # ab hier nimmt die CCU Einstellungen per MQTT an
WRITE_TIMEOUT = 10.0  # Sekunden, bis die CCU einen Schreibzugriff bestätigt haben muss
DISCOVERY_TIMEOUT = 10.0  # max. Wartezeit auf Discovery-Configs
DISCOVERY_QUIET = 2.0  # Ruhe nach der letzten Config = fertig
STALE_AFTER = 120  # Sekunden ohne Nachricht = nicht verfügbar
TICK_SECONDS = 30
TICK = "__tick__"

CLEANUP_NONE = "none"
CLEANUP_DISABLE = "disable"
CLEANUP_ENABLE = "enable"

# Gruppen: main/energy = normal sichtbar, config = Konfiguration, diag = Diagnose,
# diag_off = Diagnose und standardmäßig deaktiviert
G_MAIN, G_ENERGY, G_CONFIG, G_DIAG, G_DIAG_OFF = "main", "energy", "config", "diag", "diag_off"


class Item(NamedTuple):
    key: str
    platform: str
    de: str
    en: str
    group: str


def _c(name: str, key: str, platform: str, de: str, en: str, group: str) -> tuple[str, Item]:
    return name, Item(key, platform, de, en, group)


# Schlüssel = Name der Entity in der CCU-Autodiscovery (englisch, wie in Home Assistant sichtbar)
CATALOG: dict[str, Item] = dict(
    [
        # Einstellungen (schreibbar, mit Prüfung)
        _c("Maximum Output", "max_output", "number", "Max. Ausgangsleistung", "Maximum output", G_CONFIG),
        _c("Maximum Charging Power", "max_charge_power", "number", "Max. Ladeleistung", "Maximum charging power", G_CONFIG),
        _c("Minimum SOC", "min_soc", "number", "Mindest-Ladestand", "Minimum charge level", G_CONFIG),
        _c("Maximum SOC", "max_soc", "number", "Maximaler Ladestand", "Maximum charge level", G_CONFIG),
        _c("Meter Loss Output", "meter_loss_output", "number", "Leistung bei Zählerausfall", "Output on meter loss", G_CONFIG),
        _c("Charging Strategy", "charging_strategy", "select", "Ladestrategie", "Charging strategy", G_CONFIG),
        _c("UPS Mode", "ups_mode", "switch", "USV-Modus", "UPS mode", G_CONFIG),
        # Hauptwerte
        _c("Local Battery SOC", "soc", "sensor", "Ladestand", "State of charge", G_MAIN),
        _c("Battery Charging Power", "battery_charge_power", "sensor", "Batterie Ladeleistung", "Battery charging power", G_MAIN),
        _c("Battery Discharging Power", "battery_discharge_power", "sensor", "Batterie Entladeleistung", "Battery discharging power", G_MAIN),
        _c("CCU AC Power", "ac_power", "sensor", "CCU-Leistung (AC)", "CCU AC power", G_MAIN),
        _c("Grid Power", "grid_power", "sensor", "Netzleistung", "Grid power", G_MAIN),
        _c("PV Power", "pv_power", "sensor", "PV-Leistung", "PV power", G_MAIN),
        _c("Operating Mode", "operating_mode", "sensor", "Betriebsmodus", "Operating mode", G_MAIN),
        # Energie
        _c("CCU AC Output Energy Today", "ac_out_today", "sensor", "Abgabe heute", "Output today", G_ENERGY),
        _c("CCU AC Output Energy Total", "ac_out_total", "sensor", "Abgabe gesamt", "Output total", G_ENERGY),
        _c("CCU AC Input Energy Today", "ac_in_today", "sensor", "Aufnahme heute", "Input today", G_ENERGY),
        _c("CCU AC Input Energy Total", "ac_in_total", "sensor", "Aufnahme gesamt", "Input total", G_ENERGY),
        _c("Grid Export Energy Today", "grid_export_today", "sensor", "Netzeinspeisung heute", "Grid export today", G_ENERGY),
        _c("Grid Export Energy Total", "grid_export_total", "sensor", "Netzeinspeisung gesamt", "Grid export total", G_ENERGY),
        _c("Grid Import Energy Today", "grid_import_today", "sensor", "Netzbezug heute", "Grid import today", G_ENERGY),
        _c("Grid Import Energy Total", "grid_import_total", "sensor", "Netzbezug gesamt", "Grid import total", G_ENERGY),
        _c("PV Energy Today", "pv_energy_today", "sensor", "PV-Ertrag heute", "PV energy today", G_ENERGY),
        _c("PV Energy Total", "pv_energy_total", "sensor", "PV-Ertrag gesamt", "PV energy total", G_ENERGY),
        _c("Battery Charging Energy", "battery_charged", "sensor", "Batterie geladen", "Battery charged", G_ENERGY),
        _c("Battery Discharging Energy", "battery_discharged", "sensor", "Batterie entladen", "Battery discharged", G_ENERGY),
        # Diagnose (sichtbar)
        _c("CCU ver", "firmware", "sensor", "Firmware", "Firmware", G_DIAG),
        _c("CCU IP", "ccu_ip", "sensor", "IP-Adresse", "IP address", G_DIAG),
        _c("CCU Temperature", "temperature", "sensor", "Temperatur", "Temperature", G_DIAG),
        _c("CCU Uptime", "uptime", "sensor", "Laufzeit", "Uptime", G_DIAG),
        _c("Licence Type", "licence", "sensor", "Lizenz", "Licence", G_DIAG),
        _c("Effective Output Limit", "eff_output_limit", "sensor", "Wirksame Ausgangsgrenze", "Effective output limit", G_DIAG),
        _c("Effective Input Limit", "eff_input_limit", "sensor", "Wirksame Eingangsgrenze", "Effective input limit", G_DIAG),
        _c("Usable Energy Capacity", "usable_capacity", "sensor", "Nutzbare Kapazität", "Usable capacity", G_DIAG),
        _c("Design Energy Capacity", "design_capacity", "sensor", "Nennkapazität", "Design capacity", G_DIAG),
        _c("Available Battery Count", "battery_count", "sensor", "Anzahl Batterien", "Battery count", G_DIAG),
        _c("Inverter Fault", "inverter_fault", "binary_sensor", "Wechselrichter-Fehler", "Inverter fault", G_DIAG),
        _c("Battery Fault", "battery_fault", "binary_sensor", "Batteriefehler", "Battery fault", G_DIAG),
        _c("Meter Timeout", "meter_timeout", "binary_sensor", "Zähler-Timeout", "Meter timeout", G_DIAG),
        # Rohwerte (standardmäßig deaktiviert)
        _c("Usable Energy Remaining", "usable_energy_raw", "sensor", "Nutzbare Restenergie (Rohwert)", "Usable energy remaining (raw)", G_DIAG_OFF),
        _c("CCU ID", "ccu_id_raw", "sensor", "CCU-ID", "CCU ID", G_DIAG_OFF),
        _c("API ver", "api_ver", "sensor", "API-Version", "API version", G_DIAG_OFF),
        _c("Inv variant", "inv_variant", "sensor", "Wechselrichter-Variante", "Inverter variant", G_DIAG_OFF),
        _c("Inv DC", "inv_dc", "sensor", "Wechselrichter DC", "Inverter DC", G_DIAG_OFF),
        _c("Inv AC", "inv_ac", "sensor", "Wechselrichter AC", "Inverter AC", G_DIAG_OFF),
        _c("CCU Publication Time", "ccu_pub_time", "sensor", "CCU Meldezeit", "CCU publication time", G_DIAG_OFF),
        _c("CCU Power Age", "ccu_power_age", "sensor", "CCU Leistung Alter", "CCU power age", G_DIAG_OFF),
        _c("Backup Outlet Power", "backup_outlet_power", "sensor", "Notstrom-Steckdose Leistung", "Backup outlet power", G_DIAG_OFF),
        _c("Continuous Input Limit", "cont_input_limit", "sensor", "Dauer-Eingangsgrenze", "Continuous input limit", G_DIAG_OFF),
        _c("Multiuse System Power", "multiuse_power", "sensor", "Multiuse Systemleistung", "Multiuse system power", G_DIAG_OFF),
        _c("Multiuse System SOC", "multiuse_soc", "sensor", "Multiuse System-Ladestand", "Multiuse system SOC", G_DIAG_OFF),
        _c("Multiuse SOC Age", "multiuse_soc_age", "sensor", "Multiuse Ladestand Alter", "Multiuse SOC age", G_DIAG_OFF),
        _c("CCU Status Bits 0", "status_bits_0", "sensor", "Statusbits 0", "Status bits 0", G_DIAG_OFF),
        _c("CCU Status Bits 1", "status_bits_1", "sensor", "Statusbits 1", "Status bits 1", G_DIAG_OFF),
        _c("Grid Publication Time", "grid_pub_time", "sensor", "Netz Meldezeit", "Grid publication time", G_DIAG_OFF),
        _c("Grid Power Age", "grid_power_age", "sensor", "Netzleistung Alter", "Grid power age", G_DIAG_OFF),
        _c("Battery Publication Time", "battery_pub_time", "sensor", "Batterie Meldezeit", "Battery publication time", G_DIAG_OFF),
        _c("Converter Input Power Total", "conv_in_total", "sensor", "Wandler Eingang gesamt", "Converter input total", G_DIAG_OFF),
        _c("Converter Output Power Total", "conv_out_total", "sensor", "Wandler Ausgang gesamt", "Converter output total", G_DIAG_OFF),
        _c("Local Battery SOC Age", "soc_age", "sensor", "Ladestand Alter", "SOC age", G_DIAG_OFF),
        _c("Converter 1 Input Power", "conv1_in", "sensor", "Wandler 1 Eingang", "Converter 1 input", G_DIAG_OFF),
        _c("Converter 1 Output Power", "conv1_out", "sensor", "Wandler 1 Ausgang", "Converter 1 output", G_DIAG_OFF),
        _c("Battery 1 SOC", "bat1_soc", "sensor", "Batterie 1 Ladestand", "Battery 1 SOC", G_DIAG_OFF),
        _c("Battery 1 Voltage", "bat1_voltage", "sensor", "Batterie 1 Spannung", "Battery 1 voltage", G_DIAG_OFF),
        _c("Battery 1 PV Energy Total", "bat1_pv_total", "sensor", "Batterie 1 PV-Ertrag gesamt", "Battery 1 PV energy total", G_DIAG_OFF),
        _c("Battery 1 PV Energy Today", "bat1_pv_today", "sensor", "Batterie 1 PV-Ertrag heute", "Battery 1 PV energy today", G_DIAG_OFF),
        _c("Battery 1 PV Power", "bat1_pv_power", "sensor", "Batterie 1 PV-Leistung", "Battery 1 PV power", G_DIAG_OFF),
        _c("Battery 1 DC Power", "bat1_dc_power", "sensor", "Batterie 1 DC-Leistung", "Battery 1 DC power", G_DIAG_OFF),
        _c("Battery 1 Stored Energy", "bat1_stored", "sensor", "Batterie 1 gespeicherte Energie", "Battery 1 stored energy", G_DIAG_OFF),
        _c("Battery 1 Usable Capacity", "bat1_usable_cap", "sensor", "Batterie 1 nutzbare Kapazität", "Battery 1 usable capacity", G_DIAG_OFF),
        _c("Battery 1 Design Capacity", "bat1_design_cap", "sensor", "Batterie 1 Nennkapazität", "Battery 1 design capacity", G_DIAG_OFF),
    ]
)

# Abgeleitete Entities (berechnet die Integration selbst)
DERIVED: list[Item] = [
    Item("ac_feed_power", "sensor", "Einspeisung ins Haus", "Feed-in to house", G_MAIN),
    Item("ac_draw_power", "sensor", "AC-Aufnahme (Laden)", "AC draw (charging)", G_MAIN),
    Item("usable_energy_kwh", "sensor", "Nutzbare Restenergie", "Usable energy remaining", G_MAIN),
    Item("grid_balance", "sensor", "Netzbilanz gesamt", "Grid balance total", G_ENERGY),
    Item("battery_balance", "sensor", "Batteriebilanz gesamt", "Battery balance total", G_ENERGY),
    Item("last_update", "sensor", "Letztes Update", "Last update", G_DIAG),
    Item("full", "binary_sensor", "Speicher voll", "Battery full", G_MAIN),
    Item("empty", "binary_sensor", "Speicher leer", "Battery empty", G_MAIN),
    Item("online", "binary_sensor", "Verbunden", "Connected", G_DIAG),
    Item("write_possible", "binary_sensor", "Schreiben möglich", "Writing possible", G_DIAG),
    Item("efficiency", "sensor", "Wirkungsgrad", "Round-trip efficiency", G_ENERGY),
    Item("cycles", "sensor", "Ladezyklen", "Charge cycles", G_ENERGY),
    Item("runtime", "sensor", "Restlaufzeit", "Remaining runtime", G_MAIN),
    Item("time_to_full", "sensor", "Zeit bis voll", "Time to full", G_MAIN),
]

# Gesamtübersicht über alle CCUs (eigenes Gerät „Maxxicharge Gesamt“)
TOTAL: list[Item] = [
    Item("total_soc", "sensor", "Ladestand gesamt", "State of charge total", G_MAIN),
    Item("total_usable_energy", "sensor", "Nutzbare Restenergie gesamt", "Usable energy total", G_MAIN),
    Item("total_capacity", "sensor", "Kapazität gesamt", "Capacity total", G_DIAG),
    Item("total_battery_charge_power", "sensor", "Batterie Ladeleistung gesamt", "Battery charge power total", G_MAIN),
    Item("total_battery_discharge_power", "sensor", "Batterie Entladeleistung gesamt", "Battery discharge power total", G_MAIN),
    Item("total_pv_power", "sensor", "PV-Leistung gesamt", "PV power total", G_MAIN),
    Item("total_grid_power", "sensor", "Netzleistung", "Grid power", G_MAIN),
    Item("total_house_power", "sensor", "Hausverbrauch", "House consumption", G_MAIN),
    Item("total_ac_feed", "sensor", "Einspeisung ins Haus gesamt", "Feed-in to house total", G_MAIN),
    Item("total_ac_draw", "sensor", "AC-Aufnahme gesamt", "AC draw total", G_MAIN),
    Item("total_temperature", "sensor", "Temperatur (höchste)", "Temperature (highest)", G_DIAG),
    Item("total_pv_today", "sensor", "PV-Ertrag heute gesamt", "PV yield today total", G_ENERGY),
    Item("total_house_today", "sensor", "Hausverbrauch heute", "House consumption today", G_ENERGY),
    Item("total_autarky", "sensor", "Autarkiegrad heute", "Self-sufficiency today", G_ENERGY),
    Item("total_self_consumption", "sensor", "Eigenverbrauchsquote heute", "Self-consumption today", G_ENERGY),
    Item("total_runtime", "sensor", "Restlaufzeit gesamt", "Remaining runtime total", G_MAIN),
    Item("total_time_to_full", "sensor", "Zeit bis voll gesamt", "Time to full total", G_MAIN),
    Item("total_online", "binary_sensor", "CCUs verbunden", "CCUs connected", G_DIAG),
    Item("total_fault", "binary_sensor", "Störung", "Fault", G_DIAG),
    Item("write_lock", "switch", "Schreibschutz", "Write protection", G_CONFIG),
]

SELECT_LABELS_DE = {
    "Automatic": "Automatisch",
    "Time Plan": "Zeitplan",
    "Price Plan": "Preisplan",
}

# Betriebsmodus der CCU (kommt englisch aus der CCU) für deutsche Oberfläche; unbekannte Werte bleiben unverändert
OPERATING_MODES_DE = {
    "self consumption": "Eigenverbrauch",
    "self-consumption": "Eigenverbrauch",
    "charge": "Laden",
    "charging": "Laden",
    "discharge": "Entladen",
    "discharging": "Entladen",
    "idle": "Bereit",
    "standby": "Bereitschaft",
    "bypass": "Bypass",
    "ups": "USV",
    "ups mode": "USV-Betrieb",
    "backup": "Notstrom",
    "off": "Aus",
    "auto": "Automatisch",
    "automatic": "Automatisch",
    "fault": "Störung",
    "error": "Fehler",
    "time plan": "Zeitplan",
    "price plan": "Preisplan",
    "grid charge": "Laden aus dem Netz",
    "feed in": "Einspeisen",
    "feed-in": "Einspeisen",
    "zero feed-in": "Nulleinspeisung",
}
