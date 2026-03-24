from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from okfonts import process

FIXTURES = Path(__file__).parent / "fixtures"
SCREENSHOTS = Path(__file__).parent / "screenshots"
FONT_SIZE = 100

FONTS = sorted(FIXTURES.glob("*.woff2"))

HTML = f"""<!DOCTYPE html>
<html>
<head>
<style>
@font-face {{
  font-family: 'Original';
  src: url('/original.woff2') format('woff2');
}}
@font-face {{
  font-family: 'Processed';
  src: url('/processed.woff2') format('woff2');
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 16px;
}}
.sample {{
  font-size: {FONT_SIZE}px;
  line-height: 1;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #4f6df5;
  white-space: nowrap;
}}
.ruler {{
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: {FONT_SIZE}px;
  height: 4px;
  background: #4f6df5;
}}
</style>
</head>
<body>
  <span class="sample" style="font-family: 'Original'">Hourglass</span>
  <span class="sample" style="font-family: 'Processed'">Hourglass</span>
  <div class="ruler"></div>
</body>
</html>"""


@pytest.mark.parametrize("font_path", FONTS, ids=lambda p: p.stem)
def test_screenshot(font_path, browser, tmp_path):
    tt = TTFont(font_path)
    process(tt)
    processed_path = tmp_path / font_path.name
    tt.save(str(processed_path))

    context = browser.new_context(
        device_scale_factor=1,
        viewport={"width": 800, "height": 600},
    )
    page = context.new_page()
    page.route(
        "**/index.html",
        lambda route: route.fulfill(body=HTML, content_type="text/html"),
    )
    orig = str(font_path)
    proc = str(processed_path)
    page.route(
        "**/original.woff2",
        lambda route: route.fulfill(path=orig, content_type="font/woff2"),
    )
    page.route(
        "**/processed.woff2",
        lambda route: route.fulfill(path=proc, content_type="font/woff2"),
    )

    page.goto("http://test/index.html")
    page.evaluate("() => document.fonts.ready")

    actual = page.screenshot()
    page.close()
    context.close()

    reference = SCREENSHOTS / f"{font_path.stem}.png"
    if not reference.exists():
        SCREENSHOTS.mkdir(exist_ok=True)
        reference.write_bytes(actual)
        pytest.fail(f"Reference created: {reference.name}. Re-run to verify.")

    assert actual == reference.read_bytes(), (
        f"Screenshot mismatch for {font_path.stem}. "
        f"Delete {reference} and re-run to update."
    )
