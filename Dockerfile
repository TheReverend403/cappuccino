# syntax=docker/dockerfile:1

ARG DEBIAN_VERSION=bookworm
ARG PYTHON_VERSION=3.13

## Base
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-${DEBIAN_VERSION}-slim AS python-base

ARG META_VERSION
ARG META_VERSION_HASH
ARG META_SOURCE

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT="/venv" \
    META_VERSION="${META_VERSION}" \
    META_VERSION_HASH="${META_VERSION_HASH}" \
    META_SOURCE="${META_SOURCE}"

ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}"

WORKDIR /app

## Python builder
FROM python-base AS python-builder-base

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=LICENSE,target=LICENSE \
    uv sync --frozen --no-install-project --no-dev --group docker


## Production image
FROM python-base AS production

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5 \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder-base ${UV_PROJECT_ENVIRONMENT} ${UV_PROJECT_ENVIRONMENT}
COPY docker/rootfs /
COPY cappuccino ./cappuccino
COPY alembic ./alembic
COPY alembic.ini ./

ENV SETTINGS_FILE="/tmp/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini"

VOLUME ["/config"]
EXPOSE 1337

ENTRYPOINT ["/docker-entrypoint.sh"]
