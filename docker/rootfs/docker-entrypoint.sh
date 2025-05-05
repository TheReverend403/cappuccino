#!/bin/sh
set -eu

/docker-env2conf.py "${SETTINGS_SOURCE_FILE}" "${SETTINGS_FILE}"

alembic upgrade head

RUN_COMMAND="irc3"
if [ "${DEBUG:-false}" = "true" ]; then
    RUN_COMMAND="${RUN_COMMAND} -dr"
fi

exec ${RUN_COMMAND} "${SETTINGS_FILE}"
