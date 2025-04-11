# syntax=docker/dockerfile:1

ARG DEBIAN_VERSION=bookworm

## Base
FROM debian:${DEBIAN_VERSION}-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT="/opt/uv/venv" \
    UV_PYTHON_INSTALL_DIR="/opt/uv/python" \
    UV_CACHE_DIR="/opt/uv/cache"

ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/


## Base image
FROM python-base AS app

ARG META_VERSION
ARG META_COMMIT
ARG META_SOURCE

ENV META_VERSION="${META_VERSION}" \
    META_COMMIT="${META_COMMIT}" \
    META_SOURCE="${META_SOURCE}" \
    SETTINGS_FILE="/tmp/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini"

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5 \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=LICENSE,target=LICENSE \
    uv sync --frozen --no-install-project --no-dev --group docker

COPY docker/rootfs /
COPY cappuccino ./cappuccino
COPY alembic ./alembic
COPY alembic.ini ./

VOLUME ["/config"]
EXPOSE 1337

ENTRYPOINT ["/docker-entrypoint.sh"]
