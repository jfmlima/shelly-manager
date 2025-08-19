# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11-slim

# Build stage with uv
FROM python:${PYTHON_VERSION} AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

# Copy workspace files
COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/cli/ packages/cli/

# Install dependencies with uv
RUN uv sync --frozen --no-dev --package shelly-manager-cli

# Runtime stage
FROM python:${PYTHON_VERSION} AS runtime

# Copy uv and installed packages
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd -u 10001 -m appuser
USER appuser

ENTRYPOINT ["shelly-manager"]
