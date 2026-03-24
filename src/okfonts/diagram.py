from fontTools.ttLib import TTFont

DIM = "\033[2m"
RESET = "\033[0m"
BLUE_BG = "\033[44m"
DIM_BG = "\033[100m"  # bright black (grey) background
WHITE = "\033[97m"

ROWS = 16
BAR = "  "
EMPTY = "  "

LINE = "──"


def _to_row(val, top, span):
    return round((top - val) / span * ROWS)


def _build_column(ascender, descender, cap_height, top, span):
    """Build bar colors for a column using a shared scale."""
    asc_row = _to_row(ascender, top, span)
    cap_row = _to_row(cap_height, top, span)
    base_row = _to_row(0, top, span)
    desc_row = _to_row(descender, top, span)

    rows = []
    for r in range(ROWS):
        if r < asc_row or r >= desc_row:
            rows.append(None)
        elif cap_row <= r < base_row:
            rows.append(BLUE_BG)
        else:
            rows.append(DIM_BG)
    return rows


def _centering_label(ascender, descender, cap_height):
    """Describe how off-center capitals are within the line box."""
    top_space = ascender - cap_height
    bottom_space = -descender
    total = top_space + bottom_space
    if total == 0:
        return "centered"
    pct = abs(top_space - bottom_space) / total * 100
    if pct < 1:
        return "centered"
    return f"{pct:.0f}% off-center"


def _make_labels(ascender, descender, cap_height, top, span):
    """Build row→text dict."""
    asc_row = _to_row(ascender, top, span)
    cap_row = _to_row(cap_height, top, span)
    base_row = _to_row(0, top, span)
    desc_row = _to_row(descender, top, span)

    labels = {}

    if asc_row == cap_row:
        labels[asc_row] = f"asc = cap {ascender}"
    else:
        labels[asc_row] = f"asc {ascender}"
        labels[cap_row] = f"cap {cap_height}"

    base_r = min(base_row, ROWS) - 1
    desc_r = min(desc_row, ROWS) - 1

    if base_r == desc_r:
        labels[base_r] = f"baseline, desc {descender}"
    else:
        labels[base_r] = "baseline"
        labels[desc_r] = f"desc {descender}"

    # Centering label at the middle of the caps section
    caps_mid = (cap_row + min(base_row, ROWS) - 1) // 2
    if caps_mid not in labels:
        labels[caps_mid] = _centering_label(ascender, descender, cap_height)

    return labels


def draw_before_after(before: TTFont, after: TTFont) -> str:
    os2_b, os2_a = before["OS/2"], after["OS/2"]

    b_asc, b_desc, b_cap = os2_b.sTypoAscender, os2_b.sTypoDescender, os2_b.sCapHeight
    a_asc, a_desc, a_cap = os2_a.sTypoAscender, os2_a.sTypoDescender, os2_a.sCapHeight
    b_upm, a_upm = before["head"].unitsPerEm, after["head"].unitsPerEm

    top = max(b_asc, a_asc)
    bottom = min(b_desc, a_desc)
    span = top - bottom

    b_colors = _build_column(b_asc, b_desc, b_cap, top, span)
    a_colors = _build_column(a_asc, a_desc, a_cap, top, span)

    b_labels = _make_labels(b_asc, b_desc, b_cap, top, span)
    a_labels = _make_labels(a_asc, a_desc, a_cap, top, span)

    COL_W = 30
    lines = []

    header_l = f"  Before (UPM {b_upm})"
    header_r = f"After (UPM {a_upm})"
    lines.append(f"{header_l:<{COL_W}}{header_r}")
    lines.append("")

    for r in range(ROWS):
        b_bar = f"{b_colors[r]}{WHITE}{BAR}{RESET}" if b_colors[r] else EMPTY
        a_bar = f"{a_colors[r]}{WHITE}{BAR}{RESET}" if a_colors[r] else EMPTY

        b_lbl = f" {DIM}{LINE} {b_labels[r]}{RESET}" if r in b_labels else ""
        a_lbl = f" {DIM}{LINE} {a_labels[r]}{RESET}" if r in a_labels else ""

        left_plain = f"  {BAR}" + (f" {LINE} {b_labels[r]}" if r in b_labels else "")
        pad = COL_W - len(left_plain)
        left = f"  {b_bar}{b_lbl}" + " " * max(pad, 2)

        lines.append(f"{left}{a_bar}{a_lbl}")

    return "\n".join(lines)
