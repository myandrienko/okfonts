from base64 import b64encode
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from okfonts import process

FIXTURES = Path(__file__).parent / "fixtures"
SCREENSHOTS = Path(__file__).parent / "screenshots"
FONT_SIZE = 100
LINE_HEIGHT = 1.4
HALF_LEADING = int(FONT_SIZE * (LINE_HEIGHT - 1) / 2)

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
  gap: 40px;
}}
.sample {{
  font-size: {FONT_SIZE}px;
  line-height: 1;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #4f6df5;
  white-space: nowrap;
}}
.sample-leading {{
  font-size: {FONT_SIZE}px;
  line-height: {LINE_HEIGHT};
  background:
    linear-gradient(
      transparent {HALF_LEADING}px,
      #4f6df5 {HALF_LEADING}px,
      #4f6df5 {HALF_LEADING + 1}px,
      transparent {HALF_LEADING + 1}px,
      transparent calc(100% - {HALF_LEADING + 1}px),
      #4f6df5 calc(100% - {HALF_LEADING + 1}px),
      #4f6df5 calc(100% - {HALF_LEADING}px),
      transparent calc(100% - {HALF_LEADING}px)
    ),
    #eef2ff;
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
  <span class="sample-leading" style="font-family: 'Processed'">Hourglass</span>
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

    expected = reference.read_bytes()
    if actual != expected:
        report = _failure_report(expected, actual)
        report_path = SCREENSHOTS / f"{font_path.stem}-failure.html"
        report_path.write_text(report)
        pytest.fail(
            f"Screenshot mismatch for {font_path.stem}. "
            f"Report: {report_path}"
        )


def _failure_report(expected: bytes, actual: bytes) -> str:
    ref_b64 = b64encode(expected).decode()
    act_b64 = b64encode(actual).decode()
    return f"""<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; box-sizing: border-box; }}
body {{ font-family: system-ui; padding: 24px; background: #f5f5f5; }}
h3 {{ margin-bottom: 8px; font-size: 13px; color: #666; }}
.pair {{ display: flex; gap: 24px; margin-bottom: 24px; }}
.pair img {{ border: 1px solid #ccc; background: #fff; }}
.overlay {{ position: relative; display: inline-block; }}
.overlay img {{ display: block; border: 1px solid #ccc; }}
.overlay img:last-child {{ position: absolute; top: 0; left: 0; mix-blend-mode: difference; }}
</style>
</head>
<body>
<div class="pair">
  <div><h3>Reference</h3><img src="data:image/png;base64,{ref_b64}"></div>
  <div><h3>Actual</h3><img src="data:image/png;base64,{act_b64}"></div>
</div>
<h3>Overlay (difference)</h3>
<div class="overlay">
  <img src="data:image/png;base64,{ref_b64}">
  <img src="data:image/png;base64,{act_b64}">
</div>
</body>
</html>"""
