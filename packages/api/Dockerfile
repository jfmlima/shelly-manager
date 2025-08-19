# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11-slim

# Build stage with uv
FROM python:${PYTHON_VERSION} AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment for uv
ENV UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

# Copy workspace files
COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/api/ packages/api/

# Install dependencies with uv
RUN uv sync --frozen --no-dev --package shelly-manager-api

# Runtime stage
FROM python:${PYTHON_VERSION} AS runtime

# Copy uv and installed packages
COPY --from=builder /app/.venv /app/.venv

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0 PORT=8000 DEBUG=false

WORKDIR /app

# Non-root user
RUN useradd -u 10001 -m appuser
USER appuser

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
