# Mitmachen

Danke für dein Interesse! Fehler und Ideen gern als [Issue](https://github.com/DerSpletti/ha-maxxicharge/issues). Bitte gib Home-Assistant-Version, CCU-Firmware,
den Diagnose-Download (Eintrag → ⋮ → Diagnose herunterladen) und einen Log-Ausschnitt mit `custom_components.maxxicharge: debug` an. Entferne vorher Passwörter.

## Entwicklung
- Der Entity-Katalog steht in `custom_components/maxxicharge/const.py`. Übersetzungen entstehen daraus: `python3 scripts/generate_translations.py`
  (erzeugt `strings.json` und `translations/*.json`, nicht von Hand ändern).
- Stil: [ruff](https://docs.astral.sh/ruff/) mit der Konfiguration in `pyproject.toml` (`ruff check .`).
- Tests: siehe [tests/README.md](tests/README.md). Neue Logik bitte mit Test, möglichst in `calc.py` oder `discovery.py`, damit sie ohne Home Assistant prüfbar bleibt.
- Die Schaubilder der README entstehen mit `scripts/make_docs_images.py` (Pillow).

## Pull Requests
- Ein Thema pro Pull Request, kurz beschrieben, mit Hinweis auf getestete CCU-Firmware.
- Der Workflow (HACS-Action und hassfest) muss grün sein.
- Änderungen bitte im `CHANGELOG.md` eintragen.

## Marken
Namen, Icon und Logo von Maxxisun gehören dem Hersteller (siehe [NOTICE.md](NOTICE.md)). Bitte keine anderen Marken oder Logos ins Repository legen.
