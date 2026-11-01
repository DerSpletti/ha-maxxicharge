# Changelog

Alle wichtigen Änderungen an diesem Projekt. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [SemVer](https://semver.org/lang/de/).

## [0.9.0] – 2026-11-01
Erste veröffentlichte Version (Vorabversion auf dem Weg zu 1.0). Inoffizielle Integration für die **Maxxisun CCU V2 und V2+** per MQTT.

### Einrichtung
- **Geführter Assistent:** Willkommensseite mit allem, was man braucht (IP, Port, Benutzer, Passwort), Anleitung für die Maxxisun-App
  („Smart Home Integration“), Suche der CCUs am Broker, Auswahl.
- **Nichts extra installieren:** Ohne MQTT in Home Assistant startet die Integration einen **eigenen kleinen MQTT-Broker** (reines Python,
  MQTT 3.1.1 und 5, Login, Retained, Last Will). Ein vorhandenes MQTT (z. B. Mosquitto) wird genutzt.
- **Mehrere CCUs:** Jede CCU ist ein eigener Eintrag. Neue CCUs erscheinen später automatisch unter *Geräte & Dienste* als „Entdeckt“.
- **Fehlersuche im Dialog:** Zeigt verbundene und abgelehnte CCUs samt Grund (Benutzername, Passwort, Groß-/Kleinschreibung, Leerzeichen).
  Abgelehnte CCUs erscheinen zusätzlich unter *Reparaturen*.
- **Optionen:** Verbindungsdaten für die CCU anzeigen, Passwort des eingebauten Brokers ändern, IP, Modell festlegen, alte
  Autodiscovery-Entities deaktivieren (nichts wird gelöscht).

### Werte
- **Aufgeräumt:** Rund 70 Werte je CCU als Hauptwerte, Energie, Konfiguration und Diagnose mit deutschen Namen, ein Gerät pro CCU.
  Rohwerte (Status-Bits, Meldezeiten, Alter, Wandler-Einzelwerte) sind standardmäßig deaktiviert.
- **Abgeleitet je CCU:** Speicher voll/leer, nutzbare Restenergie in kWh, Einspeisung ins Haus, AC-Aufnahme, Netz- und Batteriebilanz,
  Wirkungsgrad, Ladezyklen, Restlaufzeit, Zeit bis voll.
- **Gesamtübersicht „Maxxicharge Gesamt“** über alle CCUs: Ladestand (nach Kapazität gewichtet), nutzbare Restenergie, Leistungen,
  Hausverbrauch, Autarkiegrad, Eigenverbrauchsquote, Restlaufzeit, Zeit bis voll, Störung, Verbindung.
- **Lesbare Anzeige:** Betriebsmodus auf Deutsch, Laufzeit als „2 Tage 1 Std 44 Min“, Ladestrategie „Dynamixx“.
- **Modellerkennung:** CCU V2 oder V2+ über `/api/info` der CCU, als Gerätemodell und Diagnose-Sensor „Modell“, von Hand änderbar.

### Einstellungen ändern
- Maximale Ausgangs- und Ladeleistung, Mindest-/Maximaler Ladestand, Leistung bei Zählerausfall, Ladestrategie und USV-Modus.
- **Geprüftes Schreiben:** Die Integration sendet, wartet bis zu 10 Sekunden auf die Rückmeldung der CCU und meldet sonst einen
  **Fehler im UI**. Die Entity zeigt immer den echten Wert.
- **Ehrliche Meldung**, wenn eine CCU eine Einstellung nie zurückmeldet (z. B. ältere Firmware): „gesendet, aber nicht bestätigt“.
- **Schreibschutz-Schalter** sperrt alle Änderungen an allen CCUs.
- Firmware unter 2.43 wird erkannt: Schreiben wird verweigert, Hinweis im Log und unter *Reparaturen*.

### Dashboard
- **Karte `custom:maxxicharge-card`** im Stil der Maxxisun-App: Haus mit PV und Speicher, Kacheln, Verlauf „Haushalt“, Kennzahlen.
- **Modular:** Bausteine (Haus-Grafik, Kacheln, Verlauf, Kennzahlen) und Kacheln einzeln wählbar, Karten-Editor mit Geräteauswahl.
- **Für jede CCU und die Gesamtübersicht**, mit **Umschalter** direkt in der Karte (Reiter pro Gerät).
- **Eigene Seite „Maxxicharge“** in der Seitenleiste mit Reitern für Gesamt, jede CCU und „Alle“. Der Knopf „Besuchen“ in den
  Geräte-Informationen jedes Geräts öffnet sie direkt.
- Beispiel-Dashboard in `examples/dashboard.yaml`.

### Diagnose und Sicherheit
- Diagnose-Download mit geschwärzten Zugangsdaten, Log-Hinweise zu Verbindung, Schreibzugriffen und Einstellungen, die eine CCU nicht
  zurückmeldet, Auflistung unbekannter Topics.
- Alles läuft lokal, keine Cloud, keine Telemetrie, keine Zusatzpakete.

### Bekannte Einschränkungen
- Einstellungen ändern geht erst ab Firmware **2.43**. Eine CCU ohne MQTT-Schnittstelle (vor 2.42.103) lässt sich nicht einbinden.
- Manche Firmware (z. B. 2.43.21) meldet Einstellungen nicht zurück. Änderungen dort können nicht bestätigt werden.
- Der eingebaute Broker und die MQTT-Verbindung der CCU sind **unverschlüsselt**: nur im Heimnetz betreiben.
- Hausverbrauch, Autarkie- und Eigenverbrauchsquote sind Näherungen. Energiezähler der CCU sind Schätzwerte.
- Das Schreiben von Einstellungen und der Betrieb mit einem vorhandenen MQTT-Broker sind auf echter Hardware noch wenig erprobt.

[0.9.0]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.9.0
