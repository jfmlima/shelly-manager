ARG PYTHON_VERSION=3.11-slim

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/cli/ packages/cli/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package shelly-manager-cli

FROM python:${PYTHON_VERSION} AS runtime

RUN useradd -u 10001 -m app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/packages/core /app/packages/core
COPY --from=builder --chown=app:app /app/packages/cli /app/packages/cli

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV SHELLY_DATA_DIR=/data SHELLY_FIRMWARE_DIR=/data/firmware

RUN mkdir -p /data/firmware && chown -R app:app /data

WORKDIR /app
USER app

ENTRYPOINT ["shelly-manager"]