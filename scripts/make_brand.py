"""Erzeugt die Marken-Bilder (Icon/Logo) für HA und HACS in custom_components/maxxicharge/brand/.

Eigenes Motiv (Sonne + Batterie in Grün) mit dem Namen „Maxxisun“ als Herstellerhinweis.
Bewusst kein Nachbau des offiziellen Maxxisun-Logos (Marke des Herstellers).
Aufruf (Pillow nötig):  python3 scripts/make_brand.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "custom_components" / "maxxicharge" / "brand"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
GREEN_A, GREEN_B = (52, 199, 89), (28, 140, 62)
SS = 4  # Supersampling für glatte Kanten


def gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(GREEN_A, GREEN_B))
    return img


def draw_icon(size: int) -> Image.Image:
    """Quadratisches Icon: grüne Kachel, Sonne über Batterie, darunter „MAXXISUN“."""
    s = size * SS
    tile = gradient(s).convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=255)
    tile.putalpha(mask)
    d = ImageDraw.Draw(tile)
    white = (255, 255, 255, 255)

    # Sonne (oben): Scheibe plus sieben Strahlen
    cx, cy, r = s / 2, s * 0.235, s * 0.080
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=white)
    w = round(s * 0.030)
    for k in range(7):
        a = math.radians(-180 + k * 30)
        x1, y1 = cx + math.cos(a) * r * 1.6, cy + math.sin(a) * r * 1.6
        x2, y2 = cx + math.cos(a) * r * 2.5, cy + math.sin(a) * r * 2.5
        d.line((x1, y1, x2, y2), fill=white, width=w)
        for x, y in ((x1, y1), (x2, y2)):
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=white)

    # Batterie (Mitte)
    bw, bh = s * 0.40, s * 0.30
    bx, by = (s - bw) / 2, s * 0.40
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=s * 0.045, fill=white)
    d.rounded_rectangle((s / 2 - s * 0.06, by - s * 0.04, s / 2 + s * 0.06, by + s * 0.01), radius=s * 0.018, fill=white)
    bar_h, gap = bh * 0.20, bh * 0.07
    for i in range(3):
        y1 = by + bh - gap - (i + 1) * bar_h - i * gap
        d.rounded_rectangle(
            (bx + bw * 0.14, y1, bx + bw * 0.86, y1 + bar_h), radius=s * 0.018, fill=(40, 160, 72, 255)
        )

    # Herstellername
    font = ImageFont.truetype(FONT, int(s * 0.125))
    text = "MAXXISUN"
    bb = d.textbbox((0, 0), text, font=font)
    d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], s * 0.775 - bb[1]), text, font=font, fill=white)
    return tile.resize((size, size), Image.LANCZOS)


def draw_logo(height: int, dark: bool) -> Image.Image:
    """Querformat: Icon, „Maxxisun“ groß, darunter „CCU2 für Home Assistant“."""
    big = ImageFont.truetype(FONT, int(height * 0.34))
    small = ImageFont.truetype(FONT, int(height * 0.15))
    t1, t2 = "Maxxisun", "CCU2 für Home Assistant"
    b1, b2 = big.getbbox(t1), small.getbbox(t2)
    pad = int(height * 0.12)
    icon = draw_icon(height - 2 * pad)
    gap = int(height * 0.04)
    block_w = max(b1[2], b2[2])
    img = Image.new("RGBA", (pad + icon.width + pad + block_w + pad, height), (0, 0, 0, 0))
    img.alpha_composite(icon, (pad, pad))
    d = ImageDraw.Draw(img)
    c1 = (52, 199, 89, 255) if dark else (28, 140, 62, 255)
    c2 = (200, 208, 203, 255) if dark else (70, 84, 76, 255)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    y0 = (height - (h1 + gap + h2)) / 2
    x = pad + icon.width + pad
    d.text((x, y0 - b1[1]), t1, font=big, fill=c1)
    d.text((x, y0 + h1 + gap - b2[1]), t2, font=small, fill=c2)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    draw_icon(256).save(OUT / "icon.png")
    draw_icon(512).save(OUT / "icon@2x.png")
    draw_icon(256).save(OUT / "dark_icon.png")
    draw_icon(512).save(OUT / "dark_icon@2x.png")
    draw_logo(128, dark=False).save(OUT / "logo.png")
    draw_logo(256, dark=False).save(OUT / "logo@2x.png")
    draw_logo(128, dark=True).save(OUT / "dark_logo.png")
    draw_logo(256, dark=True).save(OUT / "dark_logo@2x.png")
    print("ok", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
