from fontTools.ttLib import TTFont


def get_cap_height(font: TTFont) -> int:
    os2 = font["OS/2"]
    if os2.sCapHeight:
        return os2.sCapHeight
    raise ValueError("Font has no cap height defined in OS/2 table")


def process(font: TTFont) -> None:
    """Normalize font metrics so that UPM and ascender equal cap height,
    and descender is 0.

    After processing:
    - CSS font-size: Npx makes capitals exactly N pixels high
    - CSS line-height: 1 makes single-line block elements exactly N pixels high
    - Capitals are vertically centered within their lines
    """
    cap_height = get_cap_height(font)

    # Set UPM to cap height. Glyph coordinates stay unchanged —
    # this just redefines what "1 em" means relative to the glyphs.
    font["head"].unitsPerEm = cap_height

    # Set vertical metrics
    os2 = font["OS/2"]
    hhea = font["hhea"]

    os2.sTypoAscender = cap_height
    os2.sTypoDescender = 0
    os2.sTypoLineGap = 0
    os2.usWinAscent = cap_height
    os2.usWinDescent = 0

    hhea.ascent = cap_height
    hhea.descent = 0
    hhea.lineGap = 0

    # Ensure OS/2 fsSelection bit 7 (USE_TYPO_METRICS) is set
    os2.fsSelection |= 1 << 7
