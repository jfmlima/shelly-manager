FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/cli/ packages/cli/

RUN uv sync --frozen --package shelly-manager-cli

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV SHELLY_DATA_DIR=/data SHELLY_FIRMWARE_DIR=/data/firmware

ENTRYPOINT ["shelly-manager"]
