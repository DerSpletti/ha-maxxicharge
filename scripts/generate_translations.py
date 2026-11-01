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
        "user_desc": "**So verbindest du die CCU mit MQTT (einmalig):**\n\n1. Öffne in der Maxxisun-App den Bereich **Smart Home Integration** (oder im Browser `http://IP-DER-CCU/integrations/mqtt`; die Seite hat keinen Login, nur im Heimnetz verwenden).\n2. „MQTT-Verbindung“ einschalten. Broker-Adresse: `{broker}`, Port: `{port}`.\n3. „Anmeldung“ einschalten und Benutzer und Passwort eines Home-Assistant-Benutzers eintragen (am besten ein eigener Benutzer nur für MQTT).\n4. Speichern.\n\nVoraussetzung: Firmware **2.42.103 oder neuer** (Lesen), **2.43 oder neuer** zum Ändern von Einstellungen. Ist die CCU schon verbunden, klicke einfach auf „Absenden“. Die Suche dauert bis zu 10 Sekunden.",
        "prefix": "Discovery-Präfix",
        "prefix_d": "Standard ist „homeassistant“. Nur ändern, wenn die CCU anders konfiguriert ist.",
        "mq_title": "MQTT in Home Assistant einrichten",
        "mq_desc": "Die CCU spricht MQTT, dafür braucht Home Assistant einen Broker.\n\n**Noch kein Broker?** Installiere das Add-on **Mosquitto broker** (Einstellungen → Add-ons → Add-on-Store), starte es und öffne danach [die MQTT-Einrichtung](/config/integrations/dashboard/add?domain=mqtt). Dort genügt meist „Absenden“.\n\n**Schon ein Broker vorhanden?** Richte in [der MQTT-Einrichtung](/config/integrations/dashboard/add?domain=mqtt) Adresse, Port und Zugangsdaten ein.\n\nKlicke danach auf „Absenden“, ich prüfe die Verbindung erneut.",
        "nc_title": "Keine CCU gefunden",
        "nc_desc": "Am Broker hat sich keine neue CCU gemeldet. Prüfe:\n\n- Ist in der Maxxisun-App unter „Smart Home Integration“ die MQTT-Verbindung eingeschaltet und gespeichert (oben „Verbunden“)? Broker `{broker}`, Port `{port}`.\n- Stimmen Benutzer und Passwort?\n- Ist die Firmware mindestens 2.42.103?\n- Sind CCU und Home Assistant im selben Netz?\n\nNach dem Speichern an der CCU dauert es einige Sekunden, bis sie sich meldet.",
        "m_retry": "Erneut suchen",
        "m_manual": "CCU-ID manuell eingeben",
        "bc_title": "Wie soll die CCU verbunden werden?",
        "bc_desc": "In Home Assistant ist noch kein MQTT eingerichtet. Du kannst entweder den **eingebauten Broker** nutzen (nichts zu installieren) oder ein eigenes MQTT einrichten.",
        "m_embedded": "Eingebauten Broker nutzen (empfohlen, nichts installieren)",
        "m_own": "Eigenes MQTT einrichten (Anleitung)",
        "em_title": "Eingebauter MQTT-Broker",
        "em_desc": "Home Assistant startet einen kleinen MQTT-Broker, mit dem sich die CCU verbindet. Merke dir Benutzer und Passwort, du trägst sie gleich an der CCU ein. Bleibt der Port 1883 frei, ist das die beste Wahl.",
        "em_port": "Port",
        "em_user": "Benutzer",
        "em_pass": "Passwort (8–64 Zeichen: Buchstaben, Ziffern, _ . -)",
        "se_title": "CCU mit Home Assistant verbinden",
        "se_desc": "**An der CCU (einmalig):**\n\n1. Öffne in der Maxxisun-App den Bereich **Smart Home Integration** (oder im Browser `http://IP-DER-CCU/integrations/mqtt`; die Seite hat keinen Login, nur im Heimnetz verwenden).\n2. „MQTT-Verbindung“ einschalten. Broker-Adresse: `{broker}`, Port: `{port}`.\n3. „Anmeldung“ einschalten. Benutzer: `{user}`, Passwort: `{password}`.\n4. **Speichern** tippen.\n\nVoraussetzung: Firmware 2.42.103 oder neuer (Lesen), 2.43 oder neuer zum Ändern. Klicke danach auf „Absenden“. Die Suche dauert bis zu 10 Sekunden.",
        "invalid_user": "Benutzername ungültig (1–32 Zeichen: Buchstaben, Ziffern, _ . -).",
        "invalid_password": "Passwort ungültig (8–64 Zeichen: Buchstaben, Ziffern, _ . -).",
        "port_in_use": "Der Port ist schon belegt (läuft hier schon ein MQTT-Broker?). Wähle einen anderen Port oder nutze das vorhandene MQTT.",
        "e_port": "Der eingebaute MQTT-Broker konnte nicht auf Port {port} starten (Port belegt?).",
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
        "user_desc": "**How to connect the CCU to MQTT (one time):**\n\n1. In the Maxxisun app open **Smart Home Integration** (or `http://CCU-IP/integrations/mqtt` in a browser; the page has no login, use it only in your home network).\n2. Switch “MQTT connection” on. Broker address: `{broker}`, port: `{port}`.\n3. Switch “Login” on and enter user and password of a Home Assistant user (ideally a dedicated MQTT-only user).\n4. Save.\n\nRequires firmware **2.42.103 or newer** (reading) and **2.43 or newer** to change settings. If the CCU is already connected just click “Submit”. The search takes up to 10 seconds.",
        "prefix": "Discovery prefix",
        "prefix_d": "Default is “homeassistant”. Change only if your CCU uses another prefix.",
        "mq_title": "Set up MQTT in Home Assistant",
        "mq_desc": "The CCU speaks MQTT, so Home Assistant needs a broker.\n\n**No broker yet?** Install the **Mosquitto broker** add-on (Settings → Add-ons → Add-on store), start it and then open [the MQTT setup](/config/integrations/dashboard/add?domain=mqtt). Usually “Submit” is enough there.\n\n**Already have a broker?** Set up address, port and credentials in [the MQTT setup](/config/integrations/dashboard/add?domain=mqtt).\n\nThen click “Submit” and I will check the connection again.",
        "nc_title": "No CCU found",
        "nc_desc": "No new CCU announced itself on the broker. Check:\n\n- Is the MQTT connection switched on and saved in the Maxxisun app under “Smart Home Integration” (“Connected” at the top)? Broker `{broker}`, port `{port}`.\n- Are user and password correct?\n- Is the firmware at least 2.42.103?\n- Are the CCU and Home Assistant on the same network?\n\nAfter saving on the CCU it takes a few seconds until it shows up.",
        "m_retry": "Search again",
        "m_manual": "Enter CCU ID manually",
        "bc_title": "How should the CCU be connected?",
        "bc_desc": "MQTT is not set up in Home Assistant yet. You can either use the **built-in broker** (nothing to install) or set up your own MQTT.",
        "m_embedded": "Use the built-in broker (recommended, nothing to install)",
        "m_own": "Set up my own MQTT (instructions)",
        "em_title": "Built-in MQTT broker",
        "em_desc": "Home Assistant starts a small MQTT broker that the CCU connects to. Note user and password, you will enter them at the CCU in a moment. If port 1883 is free it is the best choice.",
        "em_port": "Port",
        "em_user": "User",
        "em_pass": "Password (8–64 characters: letters, digits, _ . -)",
        "se_title": "Connect the CCU to Home Assistant",
        "se_desc": "**At the CCU (one time):**\n\n1. In the Maxxisun app open **Smart Home Integration** (or `http://CCU-IP/integrations/mqtt` in a browser; the page has no login, use it only in your home network).\n2. Switch “MQTT connection” on. Broker address: `{broker}`, port: `{port}`.\n3. Switch “Login” on. User: `{user}`, password: `{password}`.\n4. Save.\n\nRequires firmware 2.42.103 or newer (reading) and 2.43 or newer to change settings. Then click “Submit”. The search takes up to 10 seconds.",
        "invalid_user": "Invalid user name (1–32 characters: letters, digits, _ . -).",
        "invalid_password": "Invalid password (8–64 characters: letters, digits, _ . -).",
        "port_in_use": "The port is already in use (is an MQTT broker already running here?). Choose another port or use the existing MQTT.",
        "e_port": "The built-in MQTT broker could not start on port {port} (port in use?).",
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
                "broker_choice": {
                    "title": t["bc_title"],
                    "description": t["bc_desc"],
                    "menu_options": {"embedded": t["m_embedded"], "mqtt_missing": t["m_own"]},
                },
                "embedded": {
                    "title": t["em_title"],
                    "description": t["em_desc"],
                    "data": {"broker_port": t["em_port"], "broker_user": t["em_user"], "broker_password": t["em_pass"]},
                },
                "search": {"title": t["se_title"], "description": t["se_desc"]},
                "mqtt_missing": {"title": t["mq_title"], "description": t["mq_desc"]},
                "no_ccu": {
                    "title": t["nc_title"],
                    "description": t["nc_desc"],
                    "menu_options": {"retry": t["m_retry"], "manual": t["m_manual"]},
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
                "invalid_user": t["invalid_user"],
                "invalid_password": t["invalid_password"],
                "port_in_use": t["port_in_use"],
            },
            "abort": {
                "mqtt_not_ready": t["mqtt_not_ready"],
                "already_configured": t["already"],
                "port_in_use": t["port_in_use"],
            },
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
            "port_in_use": {"message": t["e_port"]},
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
