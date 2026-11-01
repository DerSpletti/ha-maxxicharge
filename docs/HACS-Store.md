# Aufnahme in den offiziellen HACS-Store (hacs/default)

Voraussetzungen laut https://www.hacs.xyz/docs/publish/include/ und Stand dieses Repos:

| Anforderung | Stand |
|---|---|
| Repo öffentlich, nicht archiviert, Issues aktiv | erfüllt |
| Lizenz von GitHub als OSI-Lizenz erkannt | erfüllt (MIT) |
| `hacs.json` gültig und sortiert, mit `name` | erfüllt |
| `manifest.json` gültig, Domain kollidiert nicht mit Core | erfüllt (laut hassfest zu bestätigen) |
| Ordner `brand/` mit `icon.png` | erfüllt |
| Beschreibung des Repos (GitHub „About“) | **offen** (selbst eintragen) |
| Themen (Topics) des Repos | **offen** (selbst eintragen) |
| Workflow mit **HACS Action** und **hassfest**, beide ohne Fehler | **offen** (`docs/validate-workflow.yml` nach `.github/workflows/validate.yml` kopieren) |
| Danach ein **neues GitHub-Release** (nicht nur ein Tag) | **offen** (nach grünen Prüfungen) |
| Pull Request an `hacs/default`, nur vom Repo-Eigentümer | **offen** |

## Schritte
1. **About ausfüllen:** Repo-Seite → Zahnrad neben „About“. Beschreibung z. B.
   `Inoffizielle Home-Assistant-Integration für die Maxxisun CCU V2 und V2+ per MQTT, mit geführter Einrichtung und Dashboard-Karte.`
   Themen: `home-assistant`, `hacs`, `hacs-integration`, `maxxisun`, `maxxicharge`, `mqtt`, `battery-storage`.
2. **Workflow anlegen:** Auf GitHub „Add file → Create new file“, Pfad `.github/workflows/validate.yml`, Inhalt aus `docs/validate-workflow.yml`.
   Danach unter **Actions** abwarten, bis **Hassfest** und **HACS** grün sind. Fehler beheben (siehe Protokoll), bis beide ohne Fehler und ohne Ignores laufen.
3. **Neues Release** veröffentlichen (z. B. 0.9.1), nachdem die Prüfungen grün sind.
4. **Pull Request:**
   - `github.com/hacs/default` forken, neuen Branch anlegen (nicht `master` verwenden).
   - In der Datei `integration` den Eintrag `"DerSpletti/ha-maxxicharge"` **alphabetisch einsortiert** ergänzen.
   - PR öffnen und die **Vorlage vollständig und wahrheitsgemäß** ausfüllen (sonst wird er kommentarlos geschlossen). Der PR muss von deinem persönlichen Konto kommen, nicht von einer Organisation.
5. **Warten.** Das Review dauert laut HACS oft **Monate**. Den Stand siehst du im Backlog bei `hacs/default`. Bis dahin funktioniert die Installation weiter als „Benutzerdefiniertes Repository“.

Hinweis: Icon und Logo von Maxxisun werden mit Genehmigung des Herstellers verwendet (siehe `NOTICE.md`).
