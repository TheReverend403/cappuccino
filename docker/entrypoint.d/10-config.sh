#!/bin/sh
jinja -X "^CFG_.*" "$SETTINGS_SOURCE_FILE" > "$SETTINGS_FILE"
