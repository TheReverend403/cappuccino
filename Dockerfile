ARG PYTHON_VERSION=3.9
ARG POETRY_VERSION=1.1.12

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
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


## Python builder
FROM python-base as builder-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
        libpq-dev

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-dev
RUN pip install jinja-cli


## Production image
FROM python-base as production

COPY --from=sudobmitch/base:scratch / /
COPY docker/entrypoint.d/ /etc/entrypoint.d/

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        util-linux \
        libpq5

RUN rm -rf /var/lib/apt/lists/*

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

RUN addgroup --gid 1000 --system cappuccino && \
    adduser --uid 1000 --system --gid 1000 --no-create-home cappuccino

COPY --chown=cappuccino:cappuccino ./cappuccino /app/cappuccino
COPY --chown=cappuccino:cappuccino ./alembic /app/alembic
COPY --chown=cappuccino:cappuccino ./alembic.ini /app

VOLUME ["/config"]
VOLUME ["/data"]

EXPOSE 1337

WORKDIR /app

ENV PYTHONPATH="."
ENV SETTINGS_FILE="/data/config.ini"
ENV SETTINGS_SOURCE_FILE="/config/config.ini.j2"

ENTRYPOINT ["/usr/bin/entrypointd.sh"]
CMD ["sh", "-c", "irc3 $SETTINGS_FILE"]
