# Changelog

Alle wichtigen Änderungen an diesem Projekt. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [SemVer](https://semver.org/lang/de/).

## [0.5.0] – 2026-11-01
### Neu
- **Karte pro CCU und für die Gesamtübersicht**, im Editor per Geräteauswahl wählbar.
- **Modulare Karte:** Bausteine (Haus-Grafik, Kacheln, Verlauf, Kennzahlen) und Kacheln einzeln ein- und ausschaltbar,
  Karten-Editor mit Auswahlfeldern. Ohne Haus-Grafik werden die Kacheln als Raster angezeigt.
- **Eigene Seite „Maxxicharge“** (Seitenleiste) mit Reitern für Gesamt, jede CCU und „Alle“. Der Knopf „Besuchen“ in den
  Geräte-Informationen jedes Geräts öffnet sie direkt mit der passenden Karte.
### Geändert
- Der Link „Besuchen“ eines Geräts zeigt jetzt auf die Maxxicharge-Seite statt auf die CCU-Weboberfläche. Diese ist über
  einen Knopf auf der Seite erreichbar.

## [0.4.1] – 2026-11-01
### Geändert
- **Betriebsmodus auf Deutsch** (z. B. „Eigenverbrauch“, „Laden“), wenn Home Assistant auf Deutsch läuft. Unbekannte Werte
  bleiben unverändert.
- README mit Banner, Kartenvorschau, Schaubildern, FAQ und Liste der unterstützten Geräte (CCU V2+ unterstützt, CCU V2 ohne MQTT nicht).

## [0.4.0] – 2026-11-01
### Neu
- **Automatische Erkennung weiterer CCUs:** Meldet sich eine unbekannte CCU am Broker, erscheint sie unter
  *Geräte & Dienste* als „Entdeckt“ und lässt sich mit einem Klick einrichten.
- **Konfigurieren als Menü:** Verbindungsdaten für die CCU anzeigen (Broker, Port, Benutzer, Passwort),
  Passwort des eingebauten Brokers ändern, Einstellungen (IP, alte Entities aufräumen).
- **Reparaturhinweis**, wenn eine CCU vom eingebauten Broker abgelehnt wird (mit Grund: Benutzername oder Passwort).
- **Gesamtübersicht** („Maxxicharge Gesamt“, wird automatisch angelegt): Ladestand (kapazitätsgewichtet),
  nutzbare Restenergie, Leistungen, Hausverbrauch, Autarkiegrad, Eigenverbrauchsquote, Restlaufzeit, Zeit bis voll.
- **Kennzahlen pro CCU:** Wirkungsgrad, Ladezyklen, Restlaufzeit, Zeit bis voll.
- **Schreibschutz-Schalter**, der alle Änderungen an den CCUs sperrt.
- **Dashboard-Karte** `custom:maxxicharge-card` im Stil der Maxxisun-App (Haus, Kacheln, Verlauf), eine Datei ohne Abhängigkeiten.
### Geändert
- „AC-Aufnahme (Laden)“ zeigt `0 W` statt `-0 W`.
- Manifest: `integration_type: hub`, `loggers`.
- Dokumentation überarbeitet (Deutsch und Englisch), Lizenz und Issue-Vorlagen ergänzt.

## [0.3.6] – 2026-11-01
### Neu
- Unterstützung der **Geräte-Discovery** (`homeassistant/device/<ID>/config` mit `cmps`).
- Diagnose im Assistenten: verbundene und abgelehnte Clients, im Log die Topics nicht erkannter Meldungen.
### Geändert
- Abgelehnte Anmeldungen nennen den Grund (Benutzername, Passwort, Groß-/Kleinschreibung, Leerzeichen).

## [0.3.5] – 2026-11-01
### Geändert
- Zufallspasswort ohne leicht verwechselbare Zeichen (kein `0/O`, `1/l/I`), gut abtippbar.

## [0.3.4] – 2026-11-01
### Behoben
- Logo auf dunklem Hintergrund: Die Buchstaben waren im Original Aussparungen und verschwanden im Dunkelmodus.

## [0.3.3] – 2026-11-01
### Neu
- Icon und Logo der Hersteller-Marke im Ordner `brand/`.
- Der Assistent nennt abgelehnte CCUs am eingebauten Broker.

## [0.3.2] – 2026-11-01
### Behoben
- Einrichtungsassistent: Menüschritte brauchten eigene Methoden („Unknown error“), robustere Erkennung der
  MQTT-Integration.

## [0.3.1] – 2026-11-01
### Neu
- Willkommensseite mit allem, was man für die Einrichtung braucht (IP, Port, Benutzer, Passwort).

## [0.3.0] – 2026-11-01
### Neu
- **Eingebauter MQTT-Broker** (reines Python, MQTT 3.1.1 und 5): Es muss nichts zusätzlich installiert werden.
- Gespeicherte Entities, falls sich die CCU beim Start nicht sofort meldet.

## [0.1.0] – 2026-11-01
### Neu
- Erste Version: Entities aus der CCU-Discovery, aufgeräumt in Hauptwerte, Energie, Einstellungen und Diagnose.
- Schreiben der Einstellungen mit Prüfung der Rückmeldung (Fehler im UI statt stillem Zurückspringen).
- Abgeleitete Werte, Config- und Options-Flow, Diagnose, Firmware-Hinweis (Schreiben ab 2.43).

[0.5.0]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.5.0
[0.4.1]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.4.1
[0.4.0]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.4.0
[0.3.6]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.6
[0.3.5]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.5
[0.3.4]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.4
[0.3.3]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.3
[0.3.2]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.2
[0.3.1]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.1
[0.3.0]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.3.0
[0.1.0]: https://github.com/DerSpletti/ha-maxxicharge/releases/tag/v0.1.0
