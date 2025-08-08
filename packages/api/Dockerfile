# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11-slim

# Build wheels for core and api
FROM python:${PYTHON_VERSION} AS wheelbuilder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN pip install --upgrade pip build

# Core
COPY packages/core/pyproject.toml packages/core/README.md /build/core/
COPY packages/core/src /build/core/src
RUN cd /build/core && python -m build

# API
COPY packages/api/pyproject.toml packages/api/README.md /build/api/
COPY packages/api/src /build/api/src
RUN cd /build/api && python -m build

# Runtime
FROM python:${PYTHON_VERSION} AS runtime
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 PORT=8000 DEBUG=false
WORKDIR /app

# Non-root user
RUN useradd -u 10001 -m appuser

# Install from built wheels
COPY --from=wheelbuilder /build/core/dist/*.whl /wheels/
COPY --from=wheelbuilder /build/api/dist/*.whl /wheels/
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

EXPOSE 8000
USER appuser

# Env-driven host/port via shell expansion
CMD ["sh", "-lc", "uvicorn api.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --log-level info"]
