#!/bin/sh
echo "Interpolating env vars in /config/config.ini"
envsubst < "/config/config.ini" > "$SETTINGS_FILE"
