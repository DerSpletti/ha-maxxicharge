# Sprites aus den Hersteller-CAD-Dateien (STEP)

Ablauf (die STEP-Dateien selbst liegen nicht im Repo, zu groß):
1. `tess.py <datei.step> <mesh.json> 0.8` – STEP mit OpenCascade (`pip install cadquery-ocp pillow` in einer venv) in Dreiecke umwandeln.
   (`occt-import-js`/WASM schafft die 78-MB-Datei der CCU nicht – 0 Dreiecke.)
2. `index.html` (three.js 0.160 lokal daneben, per `python3 -m http.server`) + `shot.js` (playwright-core, System-Chromium) rendert freigestellt,
   Parameter `mesh`, `up=y|z`, `rot` (Grad um die Hochachse), Azimut -18, Elevation 32, fester Maßstab 2 px/mm.
3. Zuschneiden, für beide Geräte gleich skalieren (Faktor 74/851 Szeneneinheiten je Pixel), als WebP in `SCENE_IMG` einbetten, `w/h/fx/fy` in `SCENE` setzen.

Quellen: `battery-5kwh.step` (Up = Z, Display zeigt nach +Y → `rot=180`), `2300W_2026-05-18.stp` (CCU, Up = Y, 350 x 134 x 388 mm).
