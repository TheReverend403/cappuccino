#!/bin/sh
echo "Running database migrations"
runuser -u cappuccino -- alembic upgrade head
