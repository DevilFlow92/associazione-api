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


def sanitize_font_family(font_family: str | None) -> str | None:
    """Restituisce ``font_family`` solo se è nella whitelist dei font sicuri,
    altrimenti ``None`` (fallback al font di default)."""
    if font_family in SAFE_FONTS:
        return font_family
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
