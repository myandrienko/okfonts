# OkFonts

Make font metrics predictable on the web. Given a font file, it adjusts vertical
metrics so that:

- CSS `font-size: Npx` makes capitals exactly N pixels high
- CSS `line-height: 1` makes single-line block elements exactly N pixels high
- Capitals are perfectly centered within their lines

It does this by setting both UPM and ascender to the font's cap height, and
descender to 0. Glyph coordinates are not scaled.

Supports TTF and WOFF2.

## Install

```
uv add okfonts
```

## CLI

```
uvx okfonts input.ttf -o output.ttf
```

## Programmatic usage

```python
from fontTools.ttLib import TTFont
from okfonts import process

font = TTFont("input.ttf")
process(font)
font.save("output.ttf")
```

## Public proxy

OkFonts includes a proxy server that acts as a drop-in replacement for Google
Fonts. It intercepts CSS responses, downloads and processes every referenced
font file, and serves the result with rewritten URLs.

A public instance is available at
[okfonts.matvei.is](https://okfonts.matvei.is/v1/css2?family=Inter&display=swap).
Use it as a drop-in replacement for Google Fonts:

```html
<link
  href="https://okfonts.matvei.is/v1/css2?family=Inter&display=swap"
  rel="stylesheet"
/>
```

## Self-hosted proxy

Install with the `proxy` extra:

```
uv add 'okfonts[proxy]'
```

Run:

```
okfonts-proxy
```

The proxy exposes two routes:

- `/v1/css2` — proxies CSS requests to Google Fonts
- `/v1/font/{filename}` — serves processed font files from cache

To use it, replace `fonts.googleapis.com` with your proxy host:

```html
<link
  href="https://your-proxy/v1/css2?family=Inter&display=swap"
  rel="stylesheet"
/>
```

### Configuration

| Variable    | Default  | Description                   |
| ----------- | -------- | ----------------------------- |
| `PORT`      | `3000`   | Port the proxy listens on     |
| `CACHE_DIR` | `.cache` | Directory for processed fonts |
