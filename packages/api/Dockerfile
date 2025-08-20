ARG PYTHON_VERSION=3.11-slim

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/api/ packages/api/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package shelly-manager-api

FROM python:${PYTHON_VERSION} AS runtime

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN useradd -u 10001 -m app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/packages/core /app/packages/core
COPY --from=builder --chown=app:app /app/packages/api /app/packages/api

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0 PORT=8000 DEBUG=false

WORKDIR /app
USER app
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]