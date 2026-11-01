"""Erzeugt strings.json, translations/de.json und en.json aus dem Katalog in const.py.

Aufruf:  python3 scripts/generate_translations.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "maxxicharge"
spec = importlib.util.spec_from_file_location("mx_const", ROOT / "const.py")
const = importlib.util.module_from_spec(spec)
spec.loader.exec_module(const)

TEXT = {
    "de": {
        "user_title": "Maxxicharge einrichten",
        "user_desc": "Sucht CCUs, die sich per MQTT-Autodiscovery am Broker angemeldet haben. Die MQTT-Integration muss eingerichtet sein.",
        "prefix": "Discovery-Präfix",
        "prefix_d": "Standard ist „homeassistant“. Nur ändern, wenn die CCU anders konfiguriert ist.",
        "select_title": "CCUs auswählen",
        "select_desc": "Gefundene CCUs. Pro CCU wird ein eigener Eintrag mit aufgeräumten Entities angelegt.",
        "ccus": "CCUs",
        "manual_title": "CCU manuell angeben",
        "manual_desc": "Es wurde keine neue CCU gefunden. Gib die CCU-ID an (Format CCU2-XXXX-XXXX-XXXX). Die CCU muss ihre Discovery-Config am Broker hinterlegt haben.",
        "ccu_id": "CCU-ID",
        "ip": "IP-Adresse der CCU (optional)",
        "ip_d": "Für den lokalen Endpunkt http://<IP>/api/live und den Link im Gerät.",
        "mqtt_not_ready": "Die MQTT-Integration ist nicht eingerichtet oder nicht verbunden.",
        "already": "Alle gefundenen CCUs sind bereits eingerichtet.",
        "invalid_ccu_id": "Ungültige CCU-ID. Erwartet: CCU2-XXXX-XXXX-XXXX.",
        "cannot_connect": "Unter dieser IP antwortet keine CCU (/api/live nicht erreichbar).",
        "not_found": "Für diese CCU wurde keine Discovery-Config am Broker gefunden.",
        "none_selected": "Bitte mindestens eine CCU auswählen.",
        "opt_title": "Maxxicharge-Optionen",
        "opt_cleanup": "Alte Autodiscovery-Entities",
        "opt_cleanup_d": "Deaktiviert die doppelten Entities der CCU-Autodiscovery (nichts wird gelöscht) oder aktiviert sie wieder.",
        "c_none": "Nichts ändern",
        "c_disable": "Alte Entities deaktivieren",
        "c_enable": "Alte Entities wieder aktivieren",
        "issue_title": "CCU-Firmware zu alt zum Schreiben",
        "issue_desc": "Die CCU {ccu} hat Firmware {version}. Einstellungen lassen sich per MQTT erst ab Firmware 2.43 ändern. Lesen funktioniert weiterhin.",
        "e_mqtt": "Die MQTT-Integration ist nicht bereit.",
        "e_notfound": "CCU {ccu} hat am Broker keine Discovery-Config hinterlegt (offline?).",
        "e_nocmd": "„{name}“ ist nicht schreibbar (kein Command-Topic).",
        "e_fw": "Schreiben nicht möglich: Firmware {version} ist älter als 2.43.",
        "e_off": "Die CCU ist nicht erreichbar. „{name}“ wurde nicht geändert.",
        "e_pub": "Senden an den MQTT-Broker fehlgeschlagen („{name}“ = {value}).",
        "e_fail": "Die CCU hat „{name}“ = {value} nicht übernommen (aktueller Wert: {current}). Der Wert wurde vermutlich abgelehnt.",
        "e_opt": "Ungültige Auswahl: {option}",
    },
    "en": {
        "user_title": "Set up Maxxicharge",
        "user_desc": "Looks for CCUs that announced themselves on the broker via MQTT autodiscovery. The MQTT integration must be set up.",
        "prefix": "Discovery prefix",
        "prefix_d": "Default is “homeassistant”. Change only if your CCU uses another prefix.",
        "select_title": "Select CCUs",
        "select_desc": "CCUs found. Each CCU gets its own entry with tidy entities.",
        "ccus": "CCUs",
        "manual_title": "Enter CCU manually",
        "manual_desc": "No new CCU was found. Enter the CCU ID (format CCU2-XXXX-XXXX-XXXX). The CCU must have published its discovery config on the broker.",
        "ccu_id": "CCU ID",
        "ip": "CCU IP address (optional)",
        "ip_d": "Used for the local endpoint http://<IP>/api/live and the device link.",
        "mqtt_not_ready": "The MQTT integration is not set up or not connected.",
        "already": "All CCUs found are already set up.",
        "invalid_ccu_id": "Invalid CCU ID. Expected: CCU2-XXXX-XXXX-XXXX.",
        "cannot_connect": "No CCU answers at this IP (/api/live unreachable).",
        "not_found": "No discovery config for this CCU found on the broker.",
        "none_selected": "Please select at least one CCU.",
        "opt_title": "Maxxicharge options",
        "opt_cleanup": "Old autodiscovery entities",
        "opt_cleanup_d": "Disables the duplicate entities from the CCU autodiscovery (nothing is deleted) or re-enables them.",
        "c_none": "Change nothing",
        "c_disable": "Disable old entities",
        "c_enable": "Re-enable old entities",
        "issue_title": "CCU firmware too old for writing",
        "issue_desc": "CCU {ccu} runs firmware {version}. Settings can only be changed via MQTT from firmware 2.43. Reading still works.",
        "e_mqtt": "The MQTT integration is not ready.",
        "e_notfound": "CCU {ccu} has no discovery config on the broker (offline?).",
        "e_nocmd": "“{name}” is not writable (no command topic).",
        "e_fw": "Writing not possible: firmware {version} is older than 2.43.",
        "e_off": "The CCU is unreachable. “{name}” was not changed.",
        "e_pub": "Sending to the MQTT broker failed (“{name}” = {value}).",
        "e_fail": "The CCU did not accept “{name}” = {value} (current value: {current}). The value was probably rejected.",
        "e_opt": "Invalid selection: {option}",
    },
}


def build(lang: str) -> dict:
    t = TEXT[lang]
    entity: dict[str, dict] = {}
    for item in list(const.CATALOG.values()) + list(const.DERIVED):
        entity.setdefault(item.platform, {})[item.key] = {"name": getattr(item, lang)}
    return {
        "config": {
            "step": {
                "user": {
                    "title": t["user_title"],
                    "description": t["user_desc"],
                    "data": {"discovery_prefix": t["prefix"]},
                    "data_description": {"discovery_prefix": t["prefix_d"]},
                },
                "select": {
                    "title": t["select_title"],
                    "description": t["select_desc"],
                    "data": {"ccus": t["ccus"]},
                },
                "manual": {
                    "title": t["manual_title"],
                    "description": t["manual_desc"],
                    "data": {"ccu_id": t["ccu_id"], "ip": t["ip"]},
                    "data_description": {"ip": t["ip_d"]},
                },
            },
            "error": {
                "invalid_ccu_id": t["invalid_ccu_id"],
                "cannot_connect": t["cannot_connect"],
                "not_found": t["not_found"],
                "none_selected": t["none_selected"],
            },
            "abort": {"mqtt_not_ready": t["mqtt_not_ready"], "already_configured": t["already"]},
        },
        "options": {
            "step": {
                "init": {
                    "title": t["opt_title"],
                    "data": {"ip": t["ip"], "cleanup": t["opt_cleanup"]},
                    "data_description": {"ip": t["ip_d"], "cleanup": t["opt_cleanup_d"]},
                }
            },
            "error": {"cannot_connect": t["cannot_connect"]},
        },
        "selector": {
            "cleanup": {
                "options": {"none": t["c_none"], "disable": t["c_disable"], "enable": t["c_enable"]}
            }
        },
        "entity": entity,
        "issues": {"firmware_too_old": {"title": t["issue_title"], "description": t["issue_desc"]}},
        "exceptions": {
            "mqtt_not_ready": {"message": t["e_mqtt"]},
            "ccu_not_found": {"message": t["e_notfound"]},
            "no_command_topic": {"message": t["e_nocmd"]},
            "firmware_too_old_write": {"message": t["e_fw"]},
            "ccu_offline": {"message": t["e_off"]},
            "publish_failed": {"message": t["e_pub"]},
            "write_failed": {"message": t["e_fail"]},
            "invalid_option": {"message": t["e_opt"]},
        },
    }


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


dump(ROOT / "strings.json", build("en"))
dump(ROOT / "translations" / "en.json", build("en"))
dump(ROOT / "translations" / "de.json", build("de"))
print("ok")
