ARG ARG_PYTHON_VERSION=3.10
ARG ARG_POETRY_VERSION=1.3.1
ARG ARG_S6_OVERLAY_VERSION=3.1.2.1
ARG ARG_S6_DOWNLOAD_PATH="/opt/s6"
ARG ARG_POETRY_HOME="/opt/poetry"
ARG ARG_PYSETUP_PATH="/opt/pysetup"
ARG ARG_VENV_PATH="${ARG_PYSETUP_PATH}/.venv"


## Base
FROM python:${ARG_PYTHON_VERSION}-slim as python-base

ARG ARG_POETRY_HOME
ARG ARG_VENV_PATH

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME=${ARG_POETRY_HOME} \
    PATH="${ARG_VENV_PATH}/bin:${ARG_POETRY_HOME}/bin:$PATH"


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
ARG ARG_PYSETUP_PATH

ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=${ARG_POETRY_VERSION}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR ${ARG_PYSETUP_PATH}
COPY poetry.lock pyproject.toml ./

RUN poetry install --only main,docker


## Production image
FROM python-base as production

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq5 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG ARG_S6_DOWNLOAD_PATH
ARG ARG_VENV_PATH

COPY --from=s6-base ${ARG_S6_DOWNLOAD_PATH} /
COPY --from=builder-base ${ARG_VENV_PATH} ${ARG_VENV_PATH}
COPY docker/rootfs /

WORKDIR /app

COPY ./cappuccino ./cappuccino
COPY ./alembic ./alembic
COPY ./alembic.ini ./

ENV PYTHONPATH="." \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_READ_ONLY_ROOT=1 \
    SETTINGS_FILE="/run/config.ini" \
    SETTINGS_SOURCE_FILE="/config/config.ini"

VOLUME ["/config"]
EXPOSE 1337

ENTRYPOINT ["/init"]
