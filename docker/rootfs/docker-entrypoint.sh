#!/bin/sh
set -eu

/docker-env2conf.py "${SETTINGS_SOURCE_FILE}" "${SETTINGS_FILE}"

alembic upgrade head

exec irc3 -r "${SETTINGS_FILE}"
