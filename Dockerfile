###############################################
# Base Image
###############################################
FROM python:3.9-alpine as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.1.12 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

###############################################
# Builder Image
###############################################
FROM python-base as builder-base

RUN apk add --update-cache \
    curl \
    build-base \
    postgresql-dev

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-dev

###############################################
# Production Image
###############################################
FROM python-base as production

COPY --from=sudobmitch/base:scratch / /
COPY docker/entrypoint.d/ /etc/entrypoint.d/

RUN apk add --update-cache \
    libpq \
    sed \
    shadow \
    gettext \
    runuser

RUN rm -rf /var/cache/apk/*

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

RUN addgroup -S -g 1000 cappuccino && \
    adduser -D -S -s /sbin/nologin -G cappuccino -u 1000 cappuccino

COPY --chown=cappuccino:cappuccino ./cappuccino /app/cappuccino
COPY --chown=cappuccino:cappuccino ./alembic /app/alembic
COPY --chown=cappuccino:cappuccino ./alembic.ini /app

VOLUME ["/config"]
VOLUME ["/data"]

EXPOSE 1337

WORKDIR /app

ENV PYTHONPATH="."
ENV SETTINGS_FILE="/data/config.ini"

ENTRYPOINT ["/usr/bin/entrypointd.sh"]
CMD ["sh", "-c", "irc3 $SETTINGS_FILE"]
