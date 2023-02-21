#!/bin/sh
set -eu

cd /app || exit 1

/docker-env2conf.py "$SETTINGS_SOURCE_FILE" "$SETTINGS_FILE"
alembic upgrade head
exec irc3 "$SETTINGS_FILE"
