#!/bin/sh

echo "Interpolating env vars in $SETTINGS_SOURCE_FILE"
jinja -X "^CFG_.*" "$SETTINGS_SOURCE_FILE" > "$SETTINGS_FILE"
