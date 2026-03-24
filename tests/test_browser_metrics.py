import pytest
from conftest import FONT_SIZE, SCREENSHOTS


def load_page(page, text):
    page.goto("http://test/index.html")
    page.evaluate(
        "text => { document.getElementById('target').textContent = text }", text
    )
    page.evaluate("() => document.fonts.ready")


def test_screenshot(page, font):
    """Render a sample word for visual inspection."""
    load_page(page, "Hourglass")
    SCREENSHOTS.mkdir(exist_ok=True)
    label = "processed" if font.processed else "original"
    page.screenshot(path=str(SCREENSHOTS / f"{font.path.stem}-{label}.png"))


def test_cap_height_equals_font_size(page, font):
    """font-size: Npx should make capitals exactly N pixels high."""
    if not font.processed:
        pytest.xfail("unprocessed font: cap height != font-size")

    load_page(page, "H")

    ink_height = page.evaluate("""() => {
        const el = document.getElementById('target');
        const style = getComputedStyle(el);
        const size = 300;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        ctx.font = style.font;
        ctx.fillStyle = 'black';
        ctx.textBaseline = 'alphabetic';
        ctx.fillText('H', 10, 200);
        const data = ctx.getImageData(0, 0, size, size).data;
        let top = size, bottom = 0;
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                if (data[(y * size + x) * 4 + 3] > 0) {
                    top = Math.min(top, y);
                    bottom = Math.max(bottom, y);
                }
            }
        }
        return bottom - top + 1;
    }""")

    assert abs(ink_height - FONT_SIZE) <= 1, (
        f"expected ~{FONT_SIZE}px, got {ink_height}px"
    )


def test_line_height_equals_font_size(page, font):
    """line-height: 1 should make single-line element exactly N pixels high."""
    if not font.processed:
        pytest.xfail("unprocessed font: line height != font-size")

    load_page(page, "Discotheque")

    height = page.evaluate("""() => {
        return document.getElementById('target').getBoundingClientRect().height;
    }""")

    assert height == FONT_SIZE, f"expected {FONT_SIZE}px, got {height}px"


def test_capitals_centered(page, font):
    """Capitals should be vertically centered within their line."""
    if not font.processed:
        pytest.xfail("unprocessed font: capitals not centered")

    load_page(page, "OK")

    metrics = page.evaluate("""() => {
        const el = document.getElementById('target');
        el.style.lineHeight = '2';
        const elRect = el.getBoundingClientRect();

        // Probe the actual baseline position within the element
        const probe = document.createElement('span');
        probe.style.display = 'inline-block';
        probe.style.width = '0';
        probe.style.height = '0';
        probe.style.verticalAlign = 'baseline';
        el.appendChild(probe);
        const baseline = probe.getBoundingClientRect().top - elRect.top;
        probe.remove();

        const topLead = baseline - parseFloat(getComputedStyle(el).fontSize);
        const bottomLead = elRect.height - baseline;
        return { topLead, bottomLead };
    }""")

    assert abs(metrics["topLead"] - metrics["bottomLead"]) <= 1, (
        f"not centered: top gap {metrics['topLead']}px, bottom gap {metrics['bottomLead']}px"
    )
