#!/bin/sh
set -eu

/docker-env2conf.py "${SETTINGS_SOURCE_FILE}" "${SETTINGS_FILE}"

if [ "${SKIP_MIGRATIONS:-false}" = "false" ]; then
    alembic upgrade head
else
    echo "Skipping migrations due to SKIP_MIGRATIONS=${SKIP_MIGRATIONS}"
fi

exec irc3 "${SETTINGS_FILE}"
