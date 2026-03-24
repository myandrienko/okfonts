from dataclasses import dataclass
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

from okfonts import process


@dataclass
class FontVariant:
    path: Path
    processed: bool


FIXTURES = Path(__file__).parent / "fixtures"
SCREENSHOTS = Path(__file__).parent / "screenshots"

FONTS = sorted(FIXTURES.glob("*.woff2"))

FONT_SIZE = 100

TEST_HTML = f"""<!DOCTYPE html>
<html>
<head>
<style>
@font-face {{
  font-family: 'Test Font';
  src: url('/font.woff2') format('woff2');
}}
body {{
  margin: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}}
#target {{
  font-family: 'Test Font';
  font-size: {FONT_SIZE}px;
  line-height: 1;
  display: inline-block;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #4f6df5;
}}
#ruler {{
  position: absolute;
  left: 24px;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: {FONT_SIZE}px;
  background: #4f6df5;
}}
#ruler::before {{
  content: '{FONT_SIZE}px';
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-family: sans-serif;
  font-size: 11px;
  color: #4f6df5;
  white-space: nowrap;
}}
</style>
</head>
<body>
<div id="ruler"></div>
<span id="target"></span>
</body>
</html>"""


FONT_PARAMS = []
for font in FONTS:
    FONT_PARAMS.append(pytest.param((font, True), id=f"{font.stem}-processed"))
    FONT_PARAMS.append(pytest.param((font, False), id=f"{font.stem}-original"))


@pytest.fixture(params=FONT_PARAMS, scope="session")
def font(request, tmp_path_factory):
    """Provide a FontVariant (path + processed flag)."""
    src, do_process = request.param
    if not do_process:
        return FontVariant(path=src, processed=False)
    tt = TTFont(src)
    process(tt)
    out = tmp_path_factory.mktemp("processed") / src.name
    tt.save(str(out))
    return FontVariant(path=out, processed=True)


@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            device_scale_factor=1,
            viewport={"width": 800, "height": 600},
        )
        yield context
        browser.close()


@pytest.fixture
def page(browser_context, font):
    page = browser_context.new_page()
    page.route(
        "**/index.html",
        lambda route: route.fulfill(body=TEST_HTML, content_type="text/html"),
    )
    page.route(
        "**/font.woff2",
        lambda route: route.fulfill(
            path=str(font.path),
            content_type="font/woff2",
        ),
    )
    yield page
    page.close()
