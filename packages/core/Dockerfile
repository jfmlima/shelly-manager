ARG PYTHON_VERSION=3.11-slim

FROM python:${PYTHON_VERSION} AS wheelbuilder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build/core
RUN pip install --upgrade pip build
COPY packages/core/pyproject.toml packages/core/README.md ./
COPY packages/core/src ./src
RUN python -m build  # outputs dist/*.whl

# Usage to export wheels (optional):
# docker build -f packages/core/Dockerfile --target wheelbuilder -o ./out/core .
