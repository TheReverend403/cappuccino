ARG PYTHON_VERSION=3.9
ARG POETRY_VERSION=1.1.13

## Base
FROM python:${PYTHON_VERSION}-slim as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=$POETRY_VERSION \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    S6_DOWNLOAD_PATH="/opt/s6" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"

FROM python-base as s6-base

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    xz-utils

ARG S6_OVERLAY_VERSION="3.1.0.1"

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN mkdir -p "$S6_DOWNLOAD_PATH" && \
    tar -C "$S6_DOWNLOAD_PATH/" -Jxpf /tmp/s6-overlay-x86_64.tar.xz && \
    tar -C "$S6_DOWNLOAD_PATH/" -Jxpf /tmp/s6-overlay-noarch.tar.xz

## Python builder
FROM python-base as builder-base

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev

RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-dev && \
    pip install jinja-cli


## Production image
FROM python-base as production

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY --from=s6-base $S6_DOWNLOAD_PATH /
COPY docker/rootfs /

ARG APP_USER=app

RUN addgroup --gid 1000 --system ${APP_USER} && \
    adduser --uid 1000 --system --gid 1000 --no-create-home ${APP_USER}

COPY --chown=${APP_USER}:${APP_USER} ./cappuccino /app/cappuccino
COPY --chown=${APP_USER}:${APP_USER} ./alembic /app/alembic
COPY --chown=${APP_USER}:${APP_USER} ./alembic.ini /app

WORKDIR /app

ENV PYTHONPATH="." \
    SETTINGS_FILE="/data/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini" \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    APP_USER=${APP_USER}

VOLUME ["/config", "/data"]
EXPOSE 1337

ENTRYPOINT ["/init"]
