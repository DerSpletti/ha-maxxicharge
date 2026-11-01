# Maxxicharge für Home Assistant

[![HACS: Benutzerdefiniert](https://img.shields.io/badge/HACS-Benutzerdefiniert-41BDF5.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/DerSpletti/ha-maxxicharge)](https://github.com/DerSpletti/ha-maxxicharge/releases)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)

Inoffizielle Integration für die **Maxxisun CCU2** (Maxxicharge V2+) per MQTT. Sie bringt die CCUs mit einem
geführten Assistenten in Home Assistant und stellt die rund 70 Werte pro CCU **aufgeräumt** dar: Hauptwerte,
Energie, Einstellungen und Diagnose, mit deutschen Namen, unter einem Gerät pro CCU.

*English version: [README.en.md](README.en.md)*

> **Status: Beta.** Entwickelt und getestet mit zwei CCUs (Firmware 2.43.21 und 2.43.53) und dem eingebauten
> Broker. Das Schreiben von Einstellungen und der Betrieb mit einem vorhandenen MQTT-Broker sind auf echter
> Hardware noch wenig erprobt. Rückmeldungen sind willkommen (siehe [Fehler melden](#fehler-melden)).

## Funktionen
- **Geführte Einrichtung:** Der Assistent erklärt, was du brauchst, und findet die CCUs am Broker.
  Ist in Home Assistant noch **kein MQTT** vorhanden, bringt die Integration einen eigenen kleinen Broker mit.
  Es muss nichts zusätzlich installiert werden.
- **Mehrere CCUs:** Jede CCU ist ein eigener Eintrag. Neue CCUs werden später automatisch als „Entdeckt“ angeboten.
- **Aufgeräumt:** Hauptwerte sichtbar, Einstellungen unter „Konfiguration“, Diagnose eingeklappt, Rohwerte
  (Status-Bits, Meldezeiten, Alter, Wandler-Einzelwerte) standardmäßig deaktiviert.
- **Sicheres Schreiben:** Max. Ausgangs- und Ladeleistung, Lade-Grenzen, Leistung bei Zählerausfall,
  Ladestrategie und USV-Modus. Die Integration sendet, wartet bis zu 10 Sekunden auf die Bestätigung der CCU
  und meldet sonst einen **Fehler im UI**. Angezeigt wird immer der echte Wert der CCU.
- **Abgeleitete Werte:** Speicher voll/leer, nutzbare Restenergie in kWh, Einspeisung ins Haus, AC-Aufnahme,
  Netz- und Batteriebilanz.
- **Gesamtübersicht:** Ein Gerät **„Maxxicharge Gesamt“** rechnet über alle CCUs: Ladestand (nach Kapazität
  gewichtet), nutzbare Restenergie, Lade-/Entladeleistung, PV, Netz, **Hausverbrauch**, **Autarkiegrad**,
  **Eigenverbrauchsquote**, Restlaufzeit und Zeit bis voll. Pro CCU kommen Wirkungsgrad und Ladezyklen dazu.
- **Schreibschutz:** Ein Schalter im Gerät „Maxxicharge Gesamt“ sperrt alle Änderungen an den CCUs.
- **Eigene Dashboard-Karte** im Stil der Maxxisun-App (Haus mit PV und Speicher, Kacheln, Verlauf „Haushalt“),
  ohne Zusatzkarten. Siehe [Dashboard-Karte](#dashboard-karte).
- **Diagnose:** „Verbunden“, „Letztes Update“, Firmware, „Schreiben möglich“, Hinweis unter *Reparaturen* bei
  Firmware unter 2.43, Diagnose-Download mit geschwärzten Zugangsdaten.
- **Ohne Abhängigkeiten:** keine Zusatzpakete, kein Cloud-Konto, alles lokal.

## Voraussetzungen
- Home Assistant 2025.1 oder neuer.
- Maxxisun CCU2 mit Firmware **2.42.103** oder neuer (Lesen). **Einstellungen ändern geht erst ab 2.43.**
- Die CCU und Home Assistant sind im selben Netz.

## Installation
**HACS (empfohlen):**
[![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DerSpletti&repository=ha-maxxicharge&category=integration)
oder in HACS ⋮ → *Benutzerdefinierte Repositories* → `https://github.com/DerSpletti/ha-maxxicharge`, Kategorie
*Integration*. Dann *Maxxicharge* herunterladen und Home Assistant neu starten.

**Manuell:** Ordner `custom_components/maxxicharge` nach `<config>/custom_components/` kopieren und neu starten.

## Einrichtung
Einstellungen → Geräte & Dienste → **Integration hinzufügen → Maxxicharge**. Der Assistent führt dich durch:

1. **Willkommen:** zeigt, was du brauchst (IP von Home Assistant, Port, Benutzer, Passwort).
2. **MQTT:** Hast du schon MQTT (z. B. Mosquitto), wird es genutzt. Sonst wählst du den **eingebauten Broker**
   und legst Port, Benutzer und Passwort fest.
3. **CCU verbinden:** In der Maxxisun-App unter **Smart Home Integration** (bei jeder CCU):
   MQTT-Verbindung **an**, Broker-Adresse und Port wie angezeigt, Anmeldung **an**, Benutzer und Passwort
   eintragen, **Speichern**. Das Passwortfeld nicht leer lassen, sonst bleibt das alte Passwort gespeichert.
   (Alternativ im Browser: `http://<IP-DER-CCU>/integrations/mqtt`. Die Seite hat keinen Login, nur im Heimnetz verwenden.)
4. **Suchen und auswählen:** Die gefundenen CCUs werden angezeigt, du wählst sie aus.

Optional im Eintrag unter **Konfigurieren → Einstellungen**: die alten Autodiscovery-Entities der CCU
**deaktivieren** (nichts wird gelöscht, jederzeit rückgängig).

### Weitere CCUs später hinzufügen
Die neue CCU in der App mit den gleichen Verbindungsdaten versehen. Sie erscheint automatisch unter
*Geräte & Dienste* als „Entdeckt“. Alternativ die Integration noch einmal hinzufügen.

### Verbindungsdaten später nachlesen
Eintrag → **Konfigurieren → Verbindungsdaten für die CCU anzeigen** zeigt Broker, Port, Benutzer und Passwort
genau so, wie sie in der App einzutragen sind. Dort kannst du auch das **Passwort ändern** (gilt für alle CCUs,
danach muss es in der App bei jeder CCU neu eingetragen werden). Mit vorhandenem MQTT kennt die Integration das
Passwort nicht: Es gelten Benutzer und Passwort deines Brokers.

## Entities
| Bereich | Beispiele |
|---|---|
| Hauptwerte | Ladestand, Nutzbare Restenergie, Batterie Lade-/Entladeleistung, CCU-Leistung (AC), Netzleistung, PV-Leistung, Betriebsmodus, Speicher voll/leer |
| Energie | Abgabe/Aufnahme heute und gesamt, Netzbezug/-einspeisung, PV-Ertrag, Batterie geladen/entladen, Netz- und Batteriebilanz |
| Konfiguration | Max. Ausgangsleistung, Max. Ladeleistung, Mindest-/Maximaler Ladestand, Leistung bei Zählerausfall, Ladestrategie, USV-Modus |
| Pro CCU berechnet | Wirkungsgrad, Ladezyklen, Restlaufzeit, Zeit bis voll |
| Gesamtübersicht | Ladestand gesamt, Hausverbrauch, Autarkiegrad, Eigenverbrauchsquote, PV gesamt, Netzleistung, Schreibschutz |
| Diagnose | Verbunden, Letztes Update, Firmware, IP-Adresse, Temperatur, Laufzeit, Fehler-Flags, Schreiben möglich |

Vorzeichen der CCU: positiv = Batterie entlädt bzw. CCU speist ins Haus bzw. Netzbezug, negativ = umgekehrt.
Die Energiezähler sind **Schätzwerte**, die die CCU etwa alle 5 Minuten speichert, nicht für die Abrechnung.
Hausverbrauch, Autarkie- und Eigenverbrauchsquote sind **Näherungen** aus Zähler- und CCU-Werten. Die Gesamtübersicht
geht davon aus, dass alle CCUs am selben Zähler hängen.
Ein Beispiel-Dashboard liegt unter [`examples/dashboard.yaml`](examples/dashboard.yaml).

## Dashboard-Karte
Nach der Einrichtung steht die Karte **Maxxicharge** in der Kartenauswahl (Browser-Cache einmal neu laden, falls
sie fehlt). Per YAML:
```yaml
type: custom:maxxicharge-card
title: Maxxicharge        # optional
hours: 3                  # Zeitraum des Verlaufs in Stunden
pv_max: 4000              # Skala der Balken in W (optional)
house_max: 3000
ccu_max: 2300
```
Die Karte liest die Entities der Gesamtübersicht automatisch. Einzelne lassen sich überschreiben:
`entities: { pv: sensor.meine_pv, grid: sensor.mein_netz }`. Schlüssel: `pv`, `charge`, `discharge`, `grid`,
`house`, `soc`, `feed`, `draw`, `runtime`, `ttf`, `autarky`, `usable`, `pvtoday`, `temp`, `fault`, `lock`, `online`.

## Einstellungen ändern: was „bestätigt“ heißt
Die Integration sendet den Wert und wartet, bis die CCU ihn zurückmeldet. Das heißt: *gespeichert*, nicht
*Leistung sofort geändert*. Eine feste Zielleistung („entlade 300 W“) gibt es nicht: Die CCU regelt immer auf
ihren eigenen Zähler. Lehnt die CCU einen Wert ab oder antwortet nicht, bekommst du eine Fehlermeldung und die
Entity zeigt wieder den echten Wert.

## Bekannte Einschränkungen
- **Schreiben nur ab Firmware 2.43.** Bei älterer Firmware verweigert die Integration das mit einer
  Fehlermeldung, schreibt eine Warnung ins Log und legt einen Hinweis unter *Reparaturen* an.
- **Ältere Firmware meldet Einstellungen teils nicht zurück** (z. B. 2.43.21 bei einer der getesteten CCUs).
  Die Werte bleiben dann „unbekannt“, und ein Schreibzugriff kann nicht bestätigt werden. Ein Firmware-Update
  über die Maxxisun-App hilft.
- Die ältere Maxxicharge-V2-CCU ohne MQTT wird nicht unterstützt.
- Der **eingebaute Broker** ist bewusst klein: Anmeldung, Publish/Subscribe, Retained, Last Will, MQTT 3.1.1 und 5,
  **keine Verschlüsselung**, höchstens 20 Clients, läuft nur, solange eine CCU eingerichtet ist.
  Belegt ein anderer Dienst den Port 1883, wähle einen anderen Port oder nutze diesen Dienst.
- Die MQTT-Verbindung der CCU ist **unverschlüsselt**. Nur im vertrauenswürdigen Heimnetz betreiben.
- Alte Entity-IDs der Autodiscovery werden nicht migriert. Automationen und Dashboards müssen auf die
  neuen Entities (`sensor.ccu_xxxx_…`) umgestellt werden.

## Fehlersuche
| Problem | Lösung |
|---|---|
| Der Assistent findet keine CCU | Im Dialog stehen die mit dem Broker **verbundenen** und die **abgelehnten** CCUs samt Grund. Bei „password“ Benutzer und Passwort in der App neu eintragen (nicht leer lassen). Dann „Erneut suchen“. |
| Eine CCU steht unter *Reparaturen* als „abgelehnt“ | Zugangsdaten in der App prüfen: Eintrag → Konfigurieren → Verbindungsdaten anzeigen. |
| Werte „nicht verfügbar“ | Die CCU hat sich seit zwei Minuten nicht gemeldet. WLAN und Broker prüfen. |
| Schreiben meldet „nicht übernommen“ | Firmware 2.43 oder neuer? Meldet die CCU die Einstellung überhaupt (Wert nicht „unbekannt“)? Siehe Log. |

Für das Log in `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.maxxicharge: debug
```
Der **Diagnose-Download** (Eintrag → ⋮ → Diagnose herunterladen) enthält Topics und Werte. IP, CCU-ID und
Passwörter sind geschwärzt.

## Datenschutz und Sicherheit
- Alles läuft **lokal**. Es gibt keine Cloud-Verbindung und keine Telemetrie.
- Das Passwort des eingebauten Brokers steht in der Konfiguration der Integration, nicht in Entities. Im
  Diagnose-Download wird es geschwärzt.
- Der eingebaute Broker lauscht auf allen Netzwerkschnittstellen von Home Assistant und verlangt Anmeldung.
  Setze ihn nicht ins Internet.

## Updates und Deinstallation
Updates meldet HACS (Einstellungen → Updates). Nach dem Installieren muss Home Assistant neu gestartet werden,
das ist bei allen Integrationen so. Zum Entfernen den Eintrag löschen und in HACS deinstallieren.
Änderungen stehen im [Changelog](CHANGELOG.md).

## Fehler melden
Bitte als [GitHub-Issue](https://github.com/DerSpletti/ha-maxxicharge/issues) mit Home-Assistant-Version, CCU-Firmware,
Diagnose-Download und dem Log-Ausschnitt (Debug-Log, Passwörter entfernen).

## Entwicklung
Der Entity-Katalog steht in `custom_components/maxxicharge/const.py`. Die Übersetzungen entstehen daraus:
`python3 scripts/generate_translations.py`. Die Tests unter `tests/` brauchen `paho-mqtt` (`test_broker*.py`)
und laufen ohne Home Assistant.

## Marken und Haftung
Dies ist ein **inoffizielles** Projekt und steht in keiner Verbindung zur Maxxihandel GmbH. *Maxxisun* und
*Maxxicharge* sind Marken des Herstellers. Icon und Logo in `custom_components/maxxicharge/brand/` stammen von
maxxisun.de und dienen nur dazu, die zugehörige Hardware zu kennzeichnen. Auf Wunsch des Herstellers werden sie
entfernt. Die Nutzung erfolgt auf eigene Gefahr, das Ändern von Einstellungen am Speicher geschieht auf eigene
Verantwortung. Lizenz: [MIT](LICENSE) (gilt für den Code, nicht für die Marken).
