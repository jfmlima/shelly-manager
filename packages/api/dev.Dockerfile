FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_CACHE_DIR=/tmp/uv-cache
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/ packages/core/
COPY packages/api/ packages/api/

RUN uv sync --frozen --package shelly-manager-api

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0 PORT=8000 DEBUG=true

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]
