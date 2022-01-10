#!/bin/sh
exec runuser -u cappuccino -- alembic upgrade head
