"""Reine Rechenfunktionen (ohne Home-Assistant-Importe, damit testbar)."""

from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def weighted_soc(remaining_kwh: float | None, capacity_kwh: float | None) -> float | None:
    """Gesamt-Ladestand in % aus nutzbarer Restenergie und Kapazität (kapazitätsgewichtet)."""
    if remaining_kwh is None or not capacity_kwh or capacity_kwh <= 0:
        return None
    return round(clamp(remaining_kwh / capacity_kwh * 100, 0, 100), 1)


def house_power(grid_w: float | None, feed_w: float | None, draw_w: float | None) -> float | None:
    """Hausverbrauch = Netzbezug + Einspeisung der CCUs - Aufnahme der CCUs (Vorzeichen: Bezug positiv)."""
    if grid_w is None:
        return None
    return round(grid_w + (feed_w or 0.0) - (draw_w or 0.0), 1)


def house_energy_today(
    import_kwh: float | None, export_kwh: float | None, out_kwh: float | None, in_kwh: float | None
) -> float | None:
    """Hausverbrauch heute aus Zählerbilanz und CCU-Bilanz (Näherung)."""
    if import_kwh is None or export_kwh is None:
        return None
    return round(import_kwh - export_kwh + (out_kwh or 0.0) - (in_kwh or 0.0), 3)


def autarky(import_kwh: float | None, house_kwh: float | None) -> float | None:
    """Autarkiegrad in %: Anteil des Verbrauchs, der nicht aus dem Netz kam."""
    if import_kwh is None or house_kwh is None or house_kwh < 0.05:
        return None
    return round(clamp((1 - import_kwh / house_kwh) * 100, 0, 100), 1)


def self_consumption(export_kwh: float | None, pv_kwh: float | None) -> float | None:
    """Eigenverbrauchsquote in %: Anteil der PV-Energie, der nicht ins Netz ging (Näherung)."""
    if export_kwh is None or pv_kwh is None or pv_kwh < 0.05:
        return None
    return round(clamp((1 - export_kwh / pv_kwh) * 100, 0, 100), 1)


def efficiency(discharged_kwh: float | None, charged_kwh: float | None) -> float | None:
    """Wirkungsgrad (Entladung / Ladung) in %."""
    if discharged_kwh is None or charged_kwh is None or charged_kwh < 1.0:
        return None
    return round(clamp(discharged_kwh / charged_kwh * 100, 0, 150), 1)


def cycles(discharged_kwh: float | None, capacity_kwh: float | None) -> float | None:
    """Vollzyklen = insgesamt entladene Energie / Kapazität."""
    if discharged_kwh is None or not capacity_kwh or capacity_kwh <= 0:
        return None
    return round(discharged_kwh / capacity_kwh, 1)


def hours_left(energy_kwh: float | None, power_w: float | None, minimum_w: float = 20.0) -> float | None:
    """Stunden, bis die Energie bei konstanter Leistung aufgebraucht bzw. aufgefüllt ist."""
    if energy_kwh is None or power_w is None or power_w < minimum_w or energy_kwh < 0:
        return None
    return round(energy_kwh * 1000 / power_w, 2)


def format_duration(seconds: float | None, german: bool = True) -> str | None:
    """Sekunden lesbar umrechnen: „2 Tage 3 Std 25 Min“ bzw. „2 d 3 h 25 min“."""
    if seconds is None or seconds < 0:
        return None
    s = int(round(seconds))
    if s < 60:
        return f"{s} s"
    d, rest = divmod(s, 86400)
    h, rest = divmod(rest, 3600)
    m = rest // 60
    parts: list[str] = []
    if d:
        parts.append(f"{d} {('Tag' if d == 1 else 'Tage') if german else 'd'}")
    if d or h:
        parts.append(f"{h} {'Std' if german else 'h'}")
    parts.append(f"{m} {'Min' if german else 'min'}")
    return " ".join(parts)
