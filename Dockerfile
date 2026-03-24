FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra proxy

COPY src/ src/

ENV PORT=8080
ENV CACHE_DIR=/app/.cache
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "okfonts.proxy:app", "--host", "0.0.0.0", "--port", "8080"]
