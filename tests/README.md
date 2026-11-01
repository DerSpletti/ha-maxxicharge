# Tests

Die Tests laufen **ohne Home Assistant**: Rechenlogik, Discovery-Parser und der eingebaute MQTT-Broker (mit echten MQTT-Clients).

```bash
python3 -m venv .venv
.venv/bin/pip install paho-mqtt
PYTHON=.venv/bin/python tests/run_all.sh
```

| Datei | Prüft |
|---|---|
| `test_calc.py` | Gesamtwerte, Kennzahlen, Dauer- und Modellformatierung |
| `test_discovery.py` | Discovery-Nachrichten (Einzel- und Geräteformat) |
| `test_broker.py` | Login, Retained, Weiterleitung, Befehle, Last Will (MQTT 3.1.1 und 5) |
| `test_broker_callbacks.py` | Ablehnungsgründe, Verbindungsdaten je CCU, unbekannte Topics |
| `test_e2e.py` | simulierte CCU: Discovery gefunden, Befehl kommt an |

Jeder Test gibt `OK` oder `FAIL` je Prüfung aus und endet mit einem Fehlercode, wenn etwas fehlschlägt. Die Oberflächen von Home Assistant
(Einrichtungsassistent, Entities, Karte) sind hier nicht abgedeckt, die prüfen der Workflow (hassfest, HACS) und der Betrieb.
