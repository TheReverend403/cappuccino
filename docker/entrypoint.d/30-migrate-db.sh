#!/bin/sh
gosu "$APP_USER" alembic upgrade head
