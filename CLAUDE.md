OkFonts is a tool for making font metrics more predictable, especially when used on the web. It can be used programmatically, as a CLI tool, or as a drop-in replacement for Google Fonts.

## Basics

This is a Python 3 project managed by uv. Linted and formatted with ruff.

## How It Works

OkFonts relies on the fontTools library to manipulate font metrics. Given a font file, it:

- sets both UPM and ascender to cap height
- sets descender to 0

Glyph coordinates are not scaled. Only UPM and vertical metrics are changed.

With these changes, the following becomes true:

- When CSS `font-size` is set to N pixels, capitals are exactly N pixels high.
- When CSS `line-height` is set to 1, block elements with one line of text are exactly N pixels high.
- Capitals are perfectly centered within their lines.

Supports TTF and WOFF2.

## Tests

Screenshot tests using Playwright. Each fixture font is rendered in a browser with both original and processed variants, then compared byte-for-byte against reference PNGs in `tests/screenshots/`.

To regenerate references: delete `tests/screenshots/*.png` and run tests twice (first run creates them, second verifies). On failure, an HTML report with a diff overlay is generated alongside the reference.

Run: `uv run --group test pytest`

## CLI

Usage:

```
uvx okfonts <in> -o <out>
```

## Proxy

Proxy is a Starlette/uvicorn app, installed as an optional dependency (`proxy` extra). It proxies requests to Google Fonts. In the resulting CSS response, every mentioned font file is downloaded and processed. CSS is returned with font URLs rewritten.

Routes are prefixed with `v1/`.

Proxy respects `PORT` and `CACHE_DIR` environment variables.

## Deployment

Deployed to fly.io behind Cloudflare. Cloudflare caches both CSS (1 week) and fonts (1 year, immutable). Font cache is persisted on a fly.io volume.
