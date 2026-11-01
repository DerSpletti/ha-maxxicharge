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

## Einrichtung
1. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Maxxicharge**.
2. Discovery-Präfix bestätigen (Standard `homeassistant`).
3. Gefundene CCUs auswählen. Pro CCU entsteht ein Eintrag und ein Gerät „CCU XXXX“ (letzte 4 Zeichen der ID).
4. Optional: Eintrag → Konfigurieren → **Alte Autodiscovery-Entities deaktivieren**. Danach zeigen Dashboards
   und Automationen auf die neuen Entities (die Entity-IDs ändern sich, siehe unten).

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
