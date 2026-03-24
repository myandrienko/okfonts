import hashlib
import io
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import uvicorn
from fontTools.ttLib import TTFont
from starlette.applications import Starlette
from starlette.requests import Request as StarletteRequest
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from okfonts import process

GOOGLE_FONTS_CSS = "https://fonts.googleapis.com"
FONT_URL_RE = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+)\)")
USER_AGENT = (
    "OkFonts/0.1 (https://github.com/myandrienko/okfonts) "
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)


def get_cache_dir() -> Path:
    cache = Path(os.environ.get("CACHE_DIR", ".cache"))
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def fetch_url(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp:
        return resp.read()


def process_font(data: bytes, cache_path: Path) -> Path:
    if cache_path.exists():
        return cache_path
    tmp = cache_path.with_suffix(f".{os.getpid()}.tmp")
    font = TTFont(io.BytesIO(data))
    process(font)
    font.save(str(tmp))
    tmp.rename(cache_path)
    return cache_path


def rewrite_css(css: str) -> str:
    cache = get_cache_dir()
    urls = FONT_URL_RE.findall(css)

    for url in urls:
        key = hashlib.sha256(url.encode()).hexdigest()
        filename = f"{key}.woff2"
        cached = cache / filename

        if not cached.exists():
            data = fetch_url(url)
            process_font(data, cached)

        css = css.replace(url, f"/v1/font/{filename}")

    return css


async def serve_css(request: StarletteRequest) -> Response:
    path = request.url.path.removeprefix("/v1")
    upstream = f"{GOOGLE_FONTS_CSS}{path}?{request.url.query}"
    try:
        data = fetch_url(upstream)
    except HTTPError as e:
        return PlainTextResponse(
            f"Google Fonts responded with {e.reason}",
            status_code=e.code,
        )
    except URLError as e:
        return PlainTextResponse(
            f"Could not reach Google Fonts: {e.reason}",
            status_code=502,
        )

    css = rewrite_css(data.decode())

    return Response(
        css,
        media_type="text/css; charset=utf-8",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=604800",
        },
    )


async def serve_font(request: StarletteRequest) -> Response:
    filename = request.path_params["filename"]
    path = get_cache_dir() / filename

    if not path.exists():
        return PlainTextResponse("Not found", status_code=404)

    return Response(
        path.read_bytes(),
        media_type="font/woff2",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


app = Starlette(
    routes=[
        Route("/v1/css2", serve_css),
        Route("/v1/font/{filename}", serve_font),
    ],
)


def main():
    port = int(os.environ.get("PORT", "3000"))
    print(f"Cache directory: {get_cache_dir().resolve()}")
    uvicorn.run(app, host="0.0.0.0", port=port)
