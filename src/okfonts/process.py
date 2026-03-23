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
    old_upm = font["head"].unitsPerEm
    scale = cap_height / old_upm

    # Scale all glyphs to the new UPM
    font["head"].unitsPerEm = cap_height
    _scale_glyphs(font, scale)

    # Set vertical metrics
    os2 = font["OS/2"]
    hhea = font["hhea"]

    os2.sTypoAscender = cap_height
    os2.sTypoDescender = 0
    os2.sTypoLineGap = 0
    os2.usWinAscent = cap_height
    os2.usWinDescent = 0
    os2.sCapHeight = cap_height

    hhea.ascent = cap_height
    hhea.descent = 0
    hhea.lineGap = 0

    # Ensure OS/2 fsSelection bit 7 (USE_TYPO_METRICS) is set
    os2.fsSelection |= 1 << 7


def _scale_glyphs(font: TTFont, scale: float) -> None:
    glyf = font.get("glyf")
    if glyf is None:
        return

    for glyph_name in glyf.keys():  # noqa: SIM118
        glyph = glyf[glyph_name]

        if glyph.numberOfContours > 0:
            coords = glyph.coordinates
            glyph.coordinates = type(coords)(
                [(round(x * scale), round(y * scale)) for x, y in coords]
            )
        elif glyph.isComposite():
            for component in glyph.components:
                # Scale translation offsets in composite glyphs
                component.x = round(component.x * scale)
                component.y = round(component.y * scale)

        if hasattr(glyph, "xMin") and glyph.numberOfContours != 0:
            glyph.recalcBounds(glyf)

    # Scale horizontal metrics
    hmtx = font["hmtx"]
    for glyph_name in hmtx.metrics:
        width, lsb = hmtx.metrics[glyph_name]
        hmtx.metrics[glyph_name] = (round(width * scale), round(lsb * scale))
