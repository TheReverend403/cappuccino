ARG ARG_PYTHON_VERSION=3.9
ARG ARG_POETRY_VERSION=1.1.13
ARG ARG_S6_OVERLAY_VERSION=3.1.0.1
ARG ARG_S6_DOWNLOAD_PATH="/opt/s6"
ARG ARG_APP_USER=app


## Base
FROM python:${ARG_PYTHON_VERSION}-slim as python-base

ARG ARG_POETRY_HOME

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$VENV_PATH/bin:$POETRY_HOME/bin:$PATH"


FROM python-base as s6-base

ARG ARG_S6_OVERLAY_VERSION
ARG ARG_S6_DOWNLOAD_PATH

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    xz-utils \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://github.com/just-containers/s6-overlay/releases/download/v${ARG_S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${ARG_S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN mkdir -p "${ARG_S6_DOWNLOAD_PATH}" && \
    tar -C "${ARG_S6_DOWNLOAD_PATH}" -Jxpf /tmp/s6-overlay-x86_64.tar.xz && \
    tar -C "${ARG_S6_DOWNLOAD_PATH}" -Jxpf /tmp/s6-overlay-noarch.tar.xz


## Python builder
FROM python-base as builder-base

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG ARG_POETRY_VERSION

ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=${ARG_POETRY_VERSION}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-dev && \
    pip install jinja-cli


## Production image
FROM python-base as production

ARG ARG_S6_DOWNLOAD_PATH
ARG ARG_APP_USER

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY --from=s6-base ${ARG_S6_DOWNLOAD_PATH} /
COPY docker/rootfs /

RUN addgroup --gid 1000 --system ${ARG_APP_USER} && \
    adduser --uid 1000 --system --gid 1000 --no-create-home ${ARG_APP_USER}

WORKDIR /app

COPY --chown=${ARG_APP_USER}:${ARG_APP_USER} ./cappuccino ./cappuccino
COPY --chown=${ARG_APP_USER}:${ARG_APP_USER} ./alembic ./alembic
COPY --chown=${ARG_APP_USER}:${ARG_APP_USER} ./alembic.ini ./app

ENV PYTHONPATH="." \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    SETTINGS_FILE="/data/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini" \
    APP_USER=${ARG_APP_USER}

VOLUME ["/config", "/data"]
EXPOSE 1337

ENTRYPOINT ["/init"]
