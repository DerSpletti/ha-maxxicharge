# Maxxicharge – Maxxisun CCU2 für Home Assistant

Custom Integration für die **Maxxisun CCU2** (Maxxicharge V2+). Sie bindet die CCUs über MQTT an und
räumt dabei auf: Die rund 69 Autodiscovery-Entities pro CCU werden zu einer übersichtlichen Auswahl
(Hauptwerte, Energie, Einstellungen, Diagnose) mit deutschen Namen unter **einem** Gerät pro CCU.

## Was sie macht
- **Einrichtung per Assistent:** findet CCUs am Broker, du wählst sie aus (mehrere gleichzeitig möglich).
- **Aufgeräumt:** Hauptwerte sichtbar, Einstellungen unter „Konfiguration“, Diagnose eingeklappt,
  Rohwerte (Status-Bits, Meldezeiten, Alter, Wandler-Einzelwerte) standardmäßig deaktiviert.
- **Sicheres Schreiben:** Max. Ausgangsleistung, Max. Ladeleistung, Min./Max.-Ladestand,
  Leistung bei Zählerausfall, Ladestrategie, USV-Modus. Die Integration sendet, wartet bis zu 10 s auf
  die Bestätigung der CCU und meldet sonst einen **Fehler im UI**. Angezeigt wird immer der echte Wert der CCU.
- **Abgeleitet:** Speicher voll / leer, nutzbare Restenergie in kWh, Einspeisung ins Haus, AC-Aufnahme,
  Netzbilanz und Batteriebilanz (Gesamt).
- **Diagnose:** „Verbunden“, „Letztes Update“, Firmware, „Schreiben möglich“, Hinweis in den Reparaturen
  bei Firmware < 2.43.
- **Aufräumen der Altlasten:** Optional deaktiviert die Integration die doppelten Autodiscovery-Entities
  (nichts wird gelöscht, jederzeit rückgängig).

Wichtig: Die Integration liest Topics, Templates, Einheiten und Optionen aus den **retained Discovery-Configs**
der CCU. Es sind keine Topic-Namen fest eingebaut.

## Installation
**HACS:** HACS → ⋮ → Benutzerdefinierte Repositories → Repo-URL, Kategorie *Integration* → „Maxxicharge“
installieren → Home Assistant neu starten.

**Manuell:** Ordner `custom_components/maxxicharge` nach `<config>/custom_components/` kopieren, neu starten.

## Einrichtung von null (ohne vorhandenes MQTT)
Es muss **nichts zusätzlich installiert werden**: Ist in Home Assistant kein MQTT eingerichtet, bietet der
Assistent den **eingebauten Broker** an. Er startet im Hintergrund der Integration (reines Python, keine
Zusatzpakete), du legst nur Port, Benutzer und Passwort fest und trägst sie in der Maxxisun-App ein.
Ist MQTT (z. B. Mosquitto) schon da, nutzt die Integration dieses MQTT und startet keinen eigenen Broker.
Der eingebaute Broker ist bewusst klein: Login, Publish/Subscribe, Retained, Last Will, MQTT 3.1.1 und 5,
keine Verschlüsselung, höchstens 20 Clients. Läuft auf Port 1883 schon ein anderer Broker, wähle einen
anderen Port oder nutze diesen Broker.

Der Assistent führt dich durch alles. Du brauchst nur Home Assistant und die CCU im selben Netz.
1. **MQTT in Home Assistant:** Fehlt die MQTT-Integration, erklärt der Assistent, wie du das Add-on
   *Mosquitto broker* installierst und die MQTT-Integration einrichtest, und prüft danach erneut.
2. **CCU mit dem Broker verbinden:** Der Assistent zeigt Broker-Adresse und Port. In der Maxxisun-App öffnest du
   **Smart Home Integration** (oder im Browser `http://<IP-DER-CCU>/integrations/mqtt`), schaltest „MQTT-Verbindung“ und „Anmeldung“ ein und trägst
   Broker, Port 1883 sowie Benutzer und Passwort eines Home-Assistant-Benutzers ein (am besten ein eigener
   Benutzer nur für MQTT). Speichern.
3. **CCU finden:** Der Assistent lauscht am Broker und zeigt die gefundenen CCUs. Findet er keine, bekommt
   er Hinweise zur Fehlersuche und kann erneut suchen.

Hinweise: Benötigt Firmware ≥ 2.42.103 (Lesen), ≥ 2.43 zum Ändern. Die MQTT-Seite der CCU hat keinen
Login und MQTT läuft unverschlüsselt: nur im Heimnetz betreiben. (Der CCU-Ablauf stammt aus einem
Praxisbericht, es gibt keine offizielle Maxxisun-Doku dazu; die Feldnamen stimmen mit der Maxxisun-App überein.)

## Einrichtung
1. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Maxxicharge**.
2. Discovery-Präfix bestätigen (Standard `homeassistant`).
3. Gefundene CCUs auswählen. Pro CCU entsteht ein Eintrag und ein Gerät „CCU XXXX“ (letzte 4 Zeichen der ID).
4. Optional: Eintrag → Konfigurieren → **Alte Autodiscovery-Entities deaktivieren**. Danach zeigen Dashboards
   und Automationen auf die neuen Entities (die Entity-IDs ändern sich, siehe unten).

## Updates
Updates meldet **HACS**: Sobald im Repo ein neues Release (Tag `vX.Y.Z`, gleich der `version` in
`manifest.json`) erscheint, zeigt Home Assistant unter Einstellungen → Updates (und in HACS) ein Update
für *Maxxicharge* an. Installieren, danach Home Assistant neu starten. Wer es automatisch will, kann eine
Automation mit der Aktion `update.install` auf die Entity `update.maxxicharge_update` bauen (Neustart
bleibt nötig). Die Entity-ID kann bei dir abweichen, sie steht in HACS bzw. unter Einstellungen → Updates.

## Bekannte Einschränkungen
- **Schreiben nur ab Firmware 2.43.** Mit älterer Firmware (z. B. 2.42.103) lehnt die CCU alle Änderungen ab.
  Die Integration verweigert das dann mit Fehlermeldung, schreibt eine Warnung ins Log und legt einen Hinweis
  unter Reparaturen an.
- Eine feste Zielleistung („entlade 300 W“) gibt es nicht: Die CCU regelt immer auf ihren eigenen Zähler.
  Wer die Grenze nachführt, ändert `Max. Ausgangsleistung`.
- „Bestätigt“ heißt: Die CCU meldet den neuen Wert zurück. Ob die Leistung sich dadurch sofort ändert,
  entscheidet die CCU-Regelung.
- Energiezähler sind Schätzwerte, die die CCU etwa alle 5 Minuten speichert (nicht für Abrechnung).
- Vorzeichen der CCU: positiv = Batterie entlädt / CCU speist ins Haus / Netzbezug.
- Die ältere Maxxicharge-V2-CCU ohne MQTT wird nicht unterstützt.
- Alte Entity-IDs (`number.ccu2_maximum_output` usw.) werden nicht migriert. Automationen müssen auf
  die neuen Entities umgestellt werden (z. B. `number.ccu_06e8_max_ausgangsleistung`).
- Dieser Stand wurde nicht gegen echte Broker-Daten getestet (siehe Testanleitung).

## Testanleitung (separate Testinstanz, nicht produktiv)
1. **Laden:** `custom_components/maxxicharge` in die Testinstanz kopieren (bzw. per HACS), neu starten.
   Die Testinstanz braucht Zugriff auf den Broker. **Wichtig:** Zwei Instanzen am selben Broker sehen
   dieselben CCUs. Schreibzugriffe in der Testinstanz wirken also auch in der Produktion.
   Zum Testen daher nur unkritische Werte ändern (z. B. Max. Ladestand ±1 %).
2. **Logging** in `configuration.yaml` der Testinstanz:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.maxxicharge: debug
   ```
3. **Einrichtung prüfen:** Im Log steht „CCU … eingerichtet mit N Discovery-Entities“. Das Gerät zeigt
   die Entities in den Bereichen Steuerung / Konfiguration / Diagnose.
4. **Schreibzugriff prüfen:** Wert ändern, dann im Debug-Log nach `Schreibe … auf …` und
   `… bestätigt` suchen. Parallel zeigt `mosquitto_sub -t '<command-topic>' -v` das Kommando.
   Die Topics stehen im Diagnose-Download (Eintrag → ⋮ → Diagnose herunterladen → `entities`).
5. **Ablehnung prüfen:** Einen unzulässigen oder abgelehnten Wert setzen (z. B. mit CCU-Firmware 2.42.103).
   Erwartung: Fehlermeldung „… nicht übernommen (aktueller Wert: …)“, Entity springt auf den echten Wert zurück,
   Warnung im Log.
6. **Firmware-Hinweis:** Bei Firmware < 2.43 erscheint unter Einstellungen → Reparaturen ein Hinweis,
   „Schreiben möglich“ steht auf *Aus*.

## Entwicklung
Katalog der Entities: `custom_components/maxxicharge/const.py`. Übersetzungen werden daraus erzeugt:
`python3 scripts/generate_translations.py`.

## Marken und Haftung
Maxxisun und Maxxicharge sind Marken der Maxxihandel GmbH. Icon und Logo in `custom_components/maxxicharge/brand/`
stammen von maxxisun.de und dienen nur dazu, die zugehörige Hardware zu kennzeichnen. Dieses Projekt ist
inoffiziell und steht in keiner Verbindung zum Hersteller. Auf Wunsch des Herstellers werden die Bilder entfernt.

