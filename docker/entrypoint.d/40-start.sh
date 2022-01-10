#!/bin/sh

echo "Starting cappuccino"
exec runuser -u cappuccino -- "$@"
