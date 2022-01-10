#!/bin/sh

echo "Changing UID of cappuccino to $PUID"
usermod -u "$PUID" cappuccino
echo "Changing GID of cappuccino to $PGID"
groupmod -g "$PGID" cappuccino

echo "Changing ownership of /config, /data, /app"
chown -R cappuccino:cappuccino /config /data /app
