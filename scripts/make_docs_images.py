"""Erzeugt die Schaubilder für die README (docs/images): Banner, Einrichtung, Aufbau.

Die Bilder der Dashboard-Karte (card.png, card-states.png) sind Browser-Screenshots der Karte mit Beispieldaten.
Aufruf (Pillow nötig):  python3 scripts/make_docs_images.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "images"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
GREEN, GREEN2, BG1, BG2 = (52, 199, 89), (28, 140, 62), (8, 17, 13), (15, 42, 27)
WHITE, SOFT, DIM = (240, 245, 242), (176, 196, 184), (120, 140, 128)
SS = 2  # Supersampling


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size * SS)


def canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w * SS, h * SS), BG1)
    px = img.load()
    for y in range(h * SS):
        for x in range(w * SS):
            t = (x / (w * SS) * 0.6 + y / (h * SS) * 0.4)
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(BG1, BG2, strict=True))
    return img, ImageDraw.Draw(img)


def save(img: Image.Image, name: str, w: int, h: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    img.resize((w, h), Image.LANCZOS).save(OUT / name, optimize=True)


def rrect(d: ImageDraw.ImageDraw, box, r, fill, outline=None, width=2) -> None:
    x0, y0, x1, y1 = [v * SS for v in box]
    d.rounded_rectangle((x0, y0, x1, y1), radius=r * SS, fill=fill, outline=outline, width=width * SS)


def text(d, xy, s, f, fill, anchor="la") -> None:
    d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)


def arrow(d, x0, y0, x1, y1, color=GREEN, width=4) -> None:
    d.line((x0 * SS, y0 * SS, x1 * SS, y1 * SS), fill=color, width=width * SS)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (-1, 1):
        d.line((x1 * SS, y1 * SS, (x1 - 16 * math.cos(a + s * 0.5)) * SS, (y1 - 16 * math.sin(a + s * 0.5)) * SS),
               fill=color, width=width * SS)


def banner() -> None:
    """Banner mit dem Hersteller-Icon aus brand/ (nur zur Kennzeichnung der Hardware, siehe README)."""
    w, h = 1200, 300
    img, d = canvas(w, h)
    text(d, (272, 70), "Maxxicharge", font(BOLD, 88), WHITE)
    text(d, (276, 172), "Maxxisun CCU V2 und V2+ in Home Assistant", font(REG, 38), GREEN)
    x = 276
    for tag in ("Geführte Einrichtung", "Eingebauter Broker", "Aufgeräumte Werte", "Dashboard-Karte"):
        f = font(REG, 22)
        tw = d.textlength(tag, font=f) / SS
        rrect(d, (x, 228, x + tw + 28, 262), 17, None, outline=(70, 110, 85), width=2)
        text(d, (x + 14, 245), tag, f, SOFT, "lm")
        x += tw + 44
    save(img, "banner.png", w, h)
    out = Image.open(OUT / "banner.png").convert("RGB")
    logo = Image.open(OUT.parent.parent / "custom_components" / "maxxicharge" / "brand" / "icon@2x.png").convert("RGBA")
    size = 176
    logo = logo.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=int(size * 0.2) * 4, fill=255)
    logo.putalpha(mask.resize((size, size), Image.LANCZOS))
    out.paste(logo, (60, 62), logo)
    out.save(OUT / "banner.png", optimize=True)


def steps() -> None:
    w, h = 1200, 330
    img, d = canvas(w, h)
    data = [
        ("1", "Installieren", ["HACS öffnen,", "Maxxicharge laden,", "Home Assistant", "neu starten"]),
        ("2", "MQTT klären", ["Vorhandenes MQTT", "wird genutzt, sonst", "startet der eingebaute", "Broker"]),
        ("3", "CCU verbinden", ["In der Maxxisun-App", "unter Smart Home", "Integration Broker,", "Benutzer, Passwort"]),
        ("4", "Fertig", ["CCUs auswählen,", "Geräte, Werte und", "Dashboard-Karte", "nutzen"]),
    ]
    cw, gap, x0, y0 = 268, 32, 16, 36
    for i, (num, title, lines) in enumerate(data):
        x = x0 + i * (cw + gap)
        rrect(d, (x, y0, x + cw, y0 + 258), 22, (20, 34, 27), outline=(52, 90, 68), width=2)
        d.ellipse(((x + 20) * SS, (y0 + 20) * SS, (x + 68) * SS, (y0 + 68) * SS), fill=GREEN)
        text(d, (x + 44, y0 + 44), num, font(BOLD, 28), BG1, "mm")
        text(d, (x + 82, y0 + 44), title, font(BOLD, 26), WHITE, "lm")
        for j, ln in enumerate(lines):
            text(d, (x + 24, y0 + 98 + j * 36), ln, font(REG, 22), SOFT)
        if i < 3:
            arrow(d, x + cw + 4, y0 + 129, x + cw + gap - 4, y0 + 129)
    save(img, "setup-steps.png", w, h)


def architecture() -> None:
    w, h = 1200, 420
    img, d = canvas(w, h)

    def box(x, y, bw, bh, title, sub, accent=GREEN):
        rrect(d, (x, y, x + bw, y + bh), 18, (20, 34, 27), outline=accent, width=3)
        text(d, (x + bw / 2, y + 34), title, font(BOLD, 26), WHITE, "mm")
        for j, s_ in enumerate(sub):
            text(d, (x + bw / 2, y + 72 + j * 28), s_, font(REG, 20), SOFT, "mm")

    box(24, 48, 230, 130, "CCU 1", ["CCU V2 / V2+", "Firmware 2.42.103+"])
    box(24, 222, 230, 130, "CCU 2", ["weitere CCUs", "jederzeit möglich"])
    box(340, 107, 260, 180, "MQTT-Broker", ["eingebaut (nichts", "zu installieren)", "oder vorhandenes MQTT"], (74, 144, 226))
    box(686, 90, 228, 214, "Maxxicharge", ["liest die Discovery,", "räumt auf, rechnet,", "prüft jedes Schreiben"])
    box(992, 48, 184, 130, "Geräte", ["pro CCU und", "Gesamtübersicht"], (245, 166, 35))
    box(992, 222, 184, 130, "Dashboard", ["Karte, Energie,", "Automationen"], (169, 139, 240))
    arrow(d, 258, 118, 336, 180)
    arrow(d, 258, 282, 336, 218)
    arrow(d, 604, 197, 682, 197, (74, 144, 226))
    arrow(d, 918, 160, 988, 118, (245, 166, 35))
    arrow(d, 918, 238, 988, 280, (169, 139, 240))
    text(d, (290, 392), "WLAN · MQTT", font(REG, 20), DIM, "mm")
    text(d, (643, 222), "Werte", font(REG, 18), DIM, "mm")
    text(d, (780, 392), "Schreiben nur mit bestätigter Rückmeldung der CCU", font(REG, 20), DIM, "mm")
    save(img, "architecture.png", w, h)


if __name__ == "__main__":
    banner()
    steps()
    architecture()
    print("ok", sorted(p.name for p in OUT.iterdir()))
