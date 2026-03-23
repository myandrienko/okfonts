OkFonts is a tool for making font metrics more predictable, especially when used on the web. It can be used programmatically, as a CLI tool, or as a drop-in replacement for Google Fonts.

## Basics

This is a Python 3 project managed by uv.

## How It Works

OkFonts relies on the fontTools library to manipulate font metrics. Given a font file, it:

- sets both UPM and ascender to cap height
- sets descender to 0

With these changes, the following becomes true:

- When CSS `font-size` is set to N pixels, capitals are exactly N pixels high.
- When CSS `line-height` is set to 1, block elements with one line of text are exactly N pixels high.
- Capitals are perfectly centered within their lines.

## CLI

Usage:

```
uvx okfonts <in> -o <out>
```

## Proxy

Proxy can be installed as an extra. When started, it proxies requests to Google Fonts. In the resulting CSS response, every mentioned font file is downloaded and processed. CSS is returned with file paths rewritten.

Proxy respects `PORT` and `CACHE_DIR` environment variables.
