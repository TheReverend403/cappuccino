# syntax=docker/dockerfile:1

ARG DEBIAN_VERSION=bookworm

## Base
FROM debian:${DEBIAN_VERSION}-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1 \
    UV_PROJECT_ENVIRONMENT="/opt/uv/venv" \
    UV_PYTHON_INSTALL_DIR="/opt/uv/python" \
    UV_CACHE_DIR="/opt/uv/cache"

ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}" \
    PYTHONPATH="/app"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY .python-version .

RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    uv python install


## Base image
FROM python-base AS app

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ARG META_VERSION
ARG META_COMMIT
ARG META_SOURCE

ENV META_VERSION="${META_VERSION}" \
    META_COMMIT="${META_COMMIT}" \
    META_SOURCE="${META_SOURCE}" \
    SETTINGS_FILE="/tmp/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini"

ADD . .
RUN ln -s /app/docker/rootfs/* /

RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    uv sync --no-install-project --no-dev --group docker

VOLUME ["/config"]
EXPOSE 1337

ENTRYPOINT ["/docker-entrypoint.sh"]
