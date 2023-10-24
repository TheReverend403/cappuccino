ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=""
ARG POETRY_HOME="/opt/poetry"
ARG PYSETUP_PATH="/opt/pysetup"
ARG VENV_PATH="${PYSETUP_PATH}/.venv"


## Base
FROM python:${PYTHON_VERSION}-slim as python-base

ARG POETRY_HOME
ARG VENV_PATH

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME=${POETRY_HOME} \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=${POETRY_VERSION} \
    PATH="${VENV_PATH}/bin:${POETRY_HOME}/bin:$PATH"


## Python builder
FROM python-base as builder-base

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/*

ARG POETRY_VERSION
ARG PYSETUP_PATH

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN --mount=type=cache,target=/root/.cache \
    curl -sSL https://install.python-poetry.org | python3 -

WORKDIR ${PYSETUP_PATH}
COPY poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache \
    poetry install --only main,docker


## Production image
FROM python-base as production

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5 \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/*

ARG VENV_PATH

COPY --from=builder-base ${VENV_PATH} ${VENV_PATH}
COPY docker/rootfs /

WORKDIR /app

COPY ./cappuccino ./cappuccino
COPY ./alembic ./alembic
COPY ./alembic.ini ./

ENV PYTHONPATH="." \
    SETTINGS_FILE="/tmp/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini"

VOLUME ["/config"]
EXPOSE 1337

ENTRYPOINT ["/docker-init.sh"]
