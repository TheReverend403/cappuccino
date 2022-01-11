#!/bin/sh

if test -z "$PUID" && test -z "$PGID"; then
    echo "Neither PUID or PGID are set, skipping permission fixes."
    exit 0
fi

if test -n "$PUID"; then
    echo "Changing UID of cappuccino to $PUID"
    usermod -u "$PUID" cappuccino
fi

if test -n "$PGID"; then
    echo "Changing GID of cappuccino to $PGID"
    groupmod -g "$PGID" cappuccino
fi

echo "Changing ownership of /config, /data, /app"
chown -R cappuccino:cappuccino /config /data /app
