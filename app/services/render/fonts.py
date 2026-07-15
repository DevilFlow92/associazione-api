from __future__ import annotations

import re

# Font "web-safe" disponibili sia nei motori di rendering DOCX/PDF (Word,
# LibreOffice — usato per fallback di sostituzione metrica) sia nei browser
# (incluso Chromium headless via Playwright, dove il container potrebbe non
# avere font arbitrari installati). Limitare a questo elenco evita che un
# fontFamily preso dal JSON del template rompa silenziosamente la resa in
# uno dei due formati.
SAFE_FONTS = frozenset(
    {
        "Arial",
        "Times New Roman",
        "Calibri",
        "Georgia",
        "Verdana",
    }
)

_HEX_COLOR_PATTERN = re.compile(r"^[0-9A-Fa-f]{6}$")

MIN_FONT_SIZE_PT = 6
MAX_FONT_SIZE_PT = 96


def sanitize_font_family(font_family: str | None) -> str | None:
    """Restituisce ``font_family`` solo se è nella whitelist dei font sicuri,
    altrimenti ``None`` (fallback al font di default)."""
    if font_family in SAFE_FONTS:
        return font_family
    return None


def sanitize_font_size(font_size: object) -> float | None:
    """Restituisce ``font_size`` (in pt) solo se è un numero valido nel
    range [MIN_FONT_SIZE_PT, MAX_FONT_SIZE_PT], altrimenti ``None``
    (fallback al font size di default)."""
    if isinstance(font_size, bool) or not isinstance(font_size, int | float):
        return None
    if MIN_FONT_SIZE_PT <= font_size <= MAX_FONT_SIZE_PT:
        return float(font_size)
    return None


def validate_hex_color(color: str | None) -> str | None:
    """Valida un colore esadecimale (6 cifre hex, con o senza #).
    Restituisce il colore senza # se valido, ``None`` altrimenti."""
    if not color:
        return None
    hex_value = color.lstrip("#")
    if _HEX_COLOR_PATTERN.match(hex_value):
        return hex_value
    return None
