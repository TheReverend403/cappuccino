#!/bin/sh
runuser -u "$APP_USER" -- alembic upgrade head
