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
        "o_conn": "Verbindungsdaten für die CCU anzeigen",
        "o_set": "Einstellungen (IP, alte Entities aufräumen)",
        "o_pw": "Passwort des eingebauten Brokers ändern",
        "oc_title": "Verbindungsdaten für die CCU",
        "oc_emb": "Trage das in der Maxxisun-App unter **Smart Home Integration** ein (bei jeder CCU):\n\n- MQTT-Verbindung: **an**\n- Broker-Adresse: `{broker}`\n- Port: `{port}`\n- Anmeldung: **an**\n- Benutzername: `{user}`\n- Passwort: `{password}`\n\nDann **Speichern**. Ändert sich die Adresse von Home Assistant, musst du sie in der App anpassen.",
        "oc_ha": "Trage das in der Maxxisun-App unter **Smart Home Integration** ein (bei jeder CCU):\n\n- MQTT-Verbindung: **an**\n- Broker-Adresse: `{broker}`\n- Port: `{port}`\n- Anmeldung: **an**\n- Benutzername und Passwort: die deines MQTT-Brokers (z. B. Mosquitto). Die kennt diese Integration nicht. Den Benutzer findest du unter Einstellungen → Personen → Benutzer oder in der Konfiguration deines Brokers.\n\nDann **Speichern**.",
        "op_title": "Passwort ändern",
        "op_desc": "Das neue Passwort gilt sofort für den eingebauten Broker. **Alle CCUs** werden danach abgelehnt, bis du das neue Passwort in der Maxxisun-App bei jeder CCU einträgst (Smart Home Integration → Passwort → Speichern).",
        "dc_title": "Neue CCU gefunden",
        "dc_desc": "Die CCU `{ccu}` hat sich am Broker gemeldet. Soll sie eingerichtet werden?",
        "flow_title": "Maxxicharge {name}",
        "is_cr_title": "CCU wird vom Broker abgelehnt",
        "is_cr_desc": "Die CCU `{client}` kann sich nicht am Broker anmelden (Grund: {reason}). Prüfe in der Maxxisun-App unter Smart Home Integration Benutzer und Passwort. Die Daten findest du unter Einstellungen → Geräte & Dienste → Maxxicharge → Konfigurieren → Verbindungsdaten. Der Hinweis verschwindet, sobald sich die CCU anmelden kann.",
        "e_lock": "Schreibschutz ist eingeschaltet. „{name}“ wurde nicht geändert. Schalte den Schreibschutz im Gerät „Maxxicharge Gesamt“ aus.",
        "ot_title": "Maxxicharge Gesamt",
        "ot_desc": "Die Gesamtübersicht rechnet über alle CCUs. Hier gibt es nichts einzustellen. Der **Schreibschutz** sperrt alle Änderungen an den CCUs und sitzt als Schalter im Gerät „Maxxicharge Gesamt“.",
        "wl_title": "Willkommen bei Maxxicharge",
        "wl_desc": "Diese Einrichtung verbindet deine Maxxisun-CCU(s) per MQTT mit Home Assistant und räumt die Werte auf.\n\n**Das brauchst du gleich:**\n- **IP-Adresse von Home Assistant:** `{ha_ip}`. Das ist die „Broker-Adresse“, die du an der CCU einträgst.\n- **Port:** meist `1883`.\n- **Benutzer und Passwort für MQTT:** Hast du schon MQTT (z. B. Mosquitto), nimm dessen Zugangsdaten, am besten von einem eigenen Benutzer nur für MQTT. Sonst legst du sie im nächsten Schritt für den eingebauten Broker selbst fest.\n- **Die Maxxisun-App** (Bereich „Smart Home Integration“) oder einen Browser im Heimnetz.\n- **CCU-Firmware** 2.42.103 oder neuer zum Lesen, 2.43 oder neuer zum Ändern von Einstellungen.\n\nDie IP-Adresse der CCU brauchst du nicht, die CCUs werden automatisch gefunden. Hast du schon MQTT in Home Assistant, nutze ich es. Sonst biete ich einen eingebauten Broker an, nichts muss installiert werden.",
        "user_title": "Maxxicharge einrichten",
        "user_desc": "**So verbindest du die CCU mit MQTT (einmalig):**\n\n1. Öffne in der Maxxisun-App den Bereich **Smart Home Integration** (oder im Browser `http://IP-DER-CCU/integrations/mqtt`; die Seite hat keinen Login, nur im Heimnetz verwenden).\n2. „MQTT-Verbindung“ einschalten. Broker-Adresse: `{broker}`, Port: `{port}`.\n3. „Anmeldung“ einschalten und Benutzer und Passwort eines Home-Assistant-Benutzers eintragen (am besten ein eigener Benutzer nur für MQTT).\n4. Speichern.\n\nVoraussetzung: Firmware **2.42.103 oder neuer** (Lesen), **2.43 oder neuer** zum Ändern von Einstellungen. Ist die CCU schon verbunden, klicke einfach auf „Absenden“. Die Suche dauert bis zu 10 Sekunden.",
        "prefix": "Discovery-Präfix",
        "prefix_d": "Standard ist „homeassistant“. Nur ändern, wenn die CCU anders konfiguriert ist.",
        "mq_title": "MQTT in Home Assistant einrichten",
        "mq_desc": "Die CCU spricht MQTT, dafür braucht Home Assistant einen Broker.\n\n**Noch kein Broker?** Installiere das Add-on **Mosquitto broker** (Einstellungen → Add-ons → Add-on-Store), starte es und öffne danach [die MQTT-Einrichtung](/config/integrations/dashboard/add?domain=mqtt). Dort genügt meist „Absenden“.\n\n**Schon ein Broker vorhanden?** Richte in [der MQTT-Einrichtung](/config/integrations/dashboard/add?domain=mqtt) Adresse, Port und Zugangsdaten ein.\n\nKlicke danach auf „Absenden“, ich prüfe die Verbindung erneut.",
        "nc_title": "Keine CCU gefunden",
        "nc_desc": "Am Broker hat sich keine neue CCU gemeldet. Prüfe:\n\n- Ist in der Maxxisun-App unter „Smart Home Integration“ die MQTT-Verbindung eingeschaltet und gespeichert (oben „Verbunden“)? Broker `{broker}`, Port `{port}`.\n- Stimmen Benutzer und Passwort? Abgelehnte Anmeldungen am Broker: `{rejected}` („user“ = Benutzername falsch, „password“ = Passwort falsch). Steht hier eine CCU, trage in der Maxxisun-App Benutzer **und** Passwort neu ein (nicht leer lassen, sonst bleibt das alte Passwort).\n- Ist die Firmware mindestens 2.42.103?\n- Mit dem Broker verbunden sind: `{connected}`. Steht eine CCU hier, aber nicht in der Auswahl, hat sie noch keine Entities gemeldet (kurz warten und „Erneut suchen“).\n- Sind CCU und Home Assistant im selben Netz?\n\nNach dem Speichern an der CCU dauert es einige Sekunden, bis sie sich meldet.",
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
        "ip_d": "Wird für die Modellerkennung über die lokale Adresse der CCU (/api/info) genutzt. Normalerweise nicht nötig, die CCU meldet ihre IP selbst.",
        "mqtt_not_ready": "Die MQTT-Integration ist nicht eingerichtet oder nicht verbunden.",
        "already": "Alle gefundenen CCUs sind bereits eingerichtet.",
        "invalid_ccu_id": "Ungültige CCU-ID. Erwartet: CCU2-XXXX-XXXX-XXXX.",
        "cannot_connect": "Unter dieser IP antwortet keine CCU (/api/live nicht erreichbar).",
        "not_found": "Für diese CCU wurde keine Discovery-Config am Broker gefunden.",
        "none_selected": "Bitte mindestens eine CCU auswählen.",
        "opt_title": "Maxxicharge-Optionen",
        "opt_model": "Modell der CCU",
        "opt_model_d": "Wird normalerweise automatisch erkannt (V2 oder V2+). Nur ändern, wenn die CCU kein Modell meldet.",
        "m_auto": "Automatisch erkennen",
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
        "e_unconf": "„{name}“ = {value} wurde an die CCU gesendet, aber nicht bestätigt: Diese CCU meldet die Einstellung nicht zurück (oft ältere Firmware). Prüfe den Wert in der Maxxisun-App und aktualisiere ggf. die Firmware.",
    },
    "en": {
        "o_conn": "Show connection details for the CCU",
        "o_set": "Settings (IP, clean up old entities)",
        "o_pw": "Change password of the built-in broker",
        "oc_title": "Connection details for the CCU",
        "oc_emb": "Enter this in the Maxxisun app under **Smart Home Integration** (for every CCU):\n\n- MQTT connection: **on**\n- Broker address: `{broker}`\n- Port: `{port}`\n- Login: **on**\n- User name: `{user}`\n- Password: `{password}`\n\nThen **Save**. If the address of Home Assistant changes you must update it in the app.",
        "oc_ha": "Enter this in the Maxxisun app under **Smart Home Integration** (for every CCU):\n\n- MQTT connection: **on**\n- Broker address: `{broker}`\n- Port: `{port}`\n- Login: **on**\n- User name and password: those of your MQTT broker (e.g. Mosquitto). This integration does not know them. You find the user under Settings → People → Users or in your broker configuration.\n\nThen **Save**.",
        "op_title": "Change password",
        "op_desc": "The new password applies immediately to the built-in broker. **All CCUs** are rejected until you enter the new password in the Maxxisun app for each CCU (Smart Home Integration → Password → Save).",
        "dc_title": "New CCU found",
        "dc_desc": "The CCU `{ccu}` announced itself on the broker. Set it up?",
        "flow_title": "Maxxicharge {name}",
        "is_cr_title": "CCU rejected by the broker",
        "is_cr_desc": "The CCU `{client}` cannot log in to the broker (reason: {reason}). Check user and password in the Maxxisun app under Smart Home Integration. The details are under Settings → Devices & services → Maxxicharge → Configure → Connection details. This notice disappears as soon as the CCU can log in.",
        "e_lock": "Write protection is on. “{name}” was not changed. Turn write protection off in the device “Maxxicharge Gesamt”.",
        "ot_title": "Maxxicharge Total",
        "ot_desc": "The total overview calculates across all CCUs. There is nothing to configure here. **Write protection** blocks all changes to the CCUs and is a switch on the device “Maxxicharge Gesamt”.",
        "wl_title": "Welcome to Maxxicharge",
        "wl_desc": "This setup connects your Maxxisun CCU(s) to Home Assistant via MQTT and tidies up the values.\n\n**You will need:**\n- **IP address of Home Assistant:** `{ha_ip}`. This is the “broker address” you enter at the CCU.\n- **Port:** usually `1883`.\n- **User and password for MQTT:** if you already have MQTT (e.g. Mosquitto) use its credentials, ideally from a dedicated MQTT-only user. Otherwise you choose them yourself in the next step for the built-in broker.\n- **The Maxxisun app** (“Smart Home Integration”) or a browser in your home network.\n- **CCU firmware** 2.42.103 or newer for reading, 2.43 or newer to change settings.\n\nYou do not need the CCU’s IP address, CCUs are found automatically. If Home Assistant already has MQTT I use it. Otherwise I offer a built-in broker, nothing has to be installed.",
        "user_title": "Set up Maxxicharge",
        "user_desc": "**How to connect the CCU to MQTT (one time):**\n\n1. In the Maxxisun app open **Smart Home Integration** (or `http://CCU-IP/integrations/mqtt` in a browser; the page has no login, use it only in your home network).\n2. Switch “MQTT connection” on. Broker address: `{broker}`, port: `{port}`.\n3. Switch “Login” on and enter user and password of a Home Assistant user (ideally a dedicated MQTT-only user).\n4. Save.\n\nRequires firmware **2.42.103 or newer** (reading) and **2.43 or newer** to change settings. If the CCU is already connected just click “Submit”. The search takes up to 10 seconds.",
        "prefix": "Discovery prefix",
        "prefix_d": "Default is “homeassistant”. Change only if your CCU uses another prefix.",
        "mq_title": "Set up MQTT in Home Assistant",
        "mq_desc": "The CCU speaks MQTT, so Home Assistant needs a broker.\n\n**No broker yet?** Install the **Mosquitto broker** add-on (Settings → Add-ons → Add-on store), start it and then open [the MQTT setup](/config/integrations/dashboard/add?domain=mqtt). Usually “Submit” is enough there.\n\n**Already have a broker?** Set up address, port and credentials in [the MQTT setup](/config/integrations/dashboard/add?domain=mqtt).\n\nThen click “Submit” and I will check the connection again.",
        "nc_title": "No CCU found",
        "nc_desc": "No new CCU announced itself on the broker. Check:\n\n- Is the MQTT connection switched on and saved in the Maxxisun app under “Smart Home Integration” (“Connected” at the top)? Broker `{broker}`, port `{port}`.\n- Are user and password correct? Rejected logins at the broker: `{rejected}` (“user” = wrong user name, “password” = wrong password). If a CCU is listed, enter user **and** password again in the Maxxisun app (do not leave it empty, otherwise the old password stays).\n- Is the firmware at least 2.42.103?\n- Connected to the broker: `{connected}`. If a CCU is listed here but not offered, it has not announced its entities yet (wait a moment and “Search again”).\n- Are the CCU and Home Assistant on the same network?\n\nAfter saving on the CCU it takes a few seconds until it shows up.",
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
        "ip_d": "Used for model detection via the CCU’s local address (/api/info). Normally not needed, the CCU reports its own IP.",
        "mqtt_not_ready": "The MQTT integration is not set up or not connected.",
        "already": "All CCUs found are already set up.",
        "invalid_ccu_id": "Invalid CCU ID. Expected: CCU2-XXXX-XXXX-XXXX.",
        "cannot_connect": "No CCU answers at this IP (/api/live unreachable).",
        "not_found": "No discovery config for this CCU found on the broker.",
        "none_selected": "Please select at least one CCU.",
        "opt_title": "Maxxicharge options",
        "opt_model": "CCU model",
        "opt_model_d": "Normally detected automatically (V2 or V2+). Only change it if the CCU does not report a model.",
        "m_auto": "Detect automatically",
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
        "e_unconf": "“{name}” = {value} was sent to the CCU but not confirmed: this CCU does not report the setting back (often older firmware). Check the value in the Maxxisun app and update the firmware if needed.",
    },
}


def build(lang: str) -> dict:
    t = TEXT[lang]
    entity: dict[str, dict] = {}
    for item in list(const.CATALOG.values()) + list(const.DERIVED) + list(const.TOTAL):
        entity.setdefault(item.platform, {})[item.key] = {"name": getattr(item, lang)}
    return {
        "config": {
            "flow_title": t["flow_title"],
            "step": {
                "user": {"title": t["wl_title"], "description": t["wl_desc"]},
                "connect": {
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
                "discovery_confirm": {"title": t["dc_title"], "description": t["dc_desc"]},
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
                    "menu_options": {"connection": t["o_conn"], "settings": t["o_set"], "password": t["o_pw"]},
                },
                "connection_embedded": {"title": t["oc_title"], "description": t["oc_emb"]},
                "connection_ha": {"title": t["oc_title"], "description": t["oc_ha"]},
                "password": {
                    "title": t["op_title"],
                    "description": t["op_desc"],
                    "data": {"broker_password": t["em_pass"]},
                },
                "total_info": {"title": t["ot_title"], "description": t["ot_desc"]},
                "settings": {
                    "title": t["opt_title"],
                    "data": {"ip": t["ip"], "model": t["opt_model"], "cleanup": t["opt_cleanup"]},
                    "data_description": {"ip": t["ip_d"], "model": t["opt_model_d"], "cleanup": t["opt_cleanup_d"]},
                },
            },
            "error": {
                "cannot_connect": t["cannot_connect"],
                "invalid_password": t["invalid_password"],
                "port_in_use": t["port_in_use"],
            },
        },
        "selector": {
            "model": {"options": {"auto": t["m_auto"], "v2": "CCU V2", "v2plus": "CCU V2+"}},
            "cleanup": {
                "options": {"none": t["c_none"], "disable": t["c_disable"], "enable": t["c_enable"]}
            }
        },
        "entity": entity,
        "issues": {
            "firmware_too_old": {"title": t["issue_title"], "description": t["issue_desc"]},
            "client_rejected": {"title": t["is_cr_title"], "description": t["is_cr_desc"]},
        },
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
            "write_locked": {"message": t["e_lock"]},
            "write_unconfirmed": {"message": t["e_unconf"]},
        },
    }


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


dump(ROOT / "strings.json", build("en"))
dump(ROOT / "translations" / "en.json", build("en"))
dump(ROOT / "translations" / "de.json", build("de"))
print("ok")
