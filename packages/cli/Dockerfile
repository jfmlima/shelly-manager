# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11-slim

# Build wheels for core and cli
FROM python:${PYTHON_VERSION} AS wheelbuilder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN pip install --upgrade pip build

# Core
COPY packages/core/pyproject.toml packages/core/README.md /build/core/
COPY packages/core/src /build/core/src
RUN cd /build/core && python -m build

# CLI
COPY packages/cli/pyproject.toml packages/cli/README.md /build/cli/
COPY packages/cli/src /build/cli/src
RUN cd /build/cli && python -m build

# Runtime
FROM python:${PYTHON_VERSION} AS runtime
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd -u 10001 -m appuser
COPY --from=wheelbuilder /build/core/dist/*.whl /wheels/
COPY --from=wheelbuilder /build/cli/dist/*.whl /wheels/
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
USER appuser

ENTRYPOINT ["shelly-manager"]
