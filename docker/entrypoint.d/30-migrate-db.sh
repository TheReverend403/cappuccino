#!/bin/sh
sudo -E -u cappuccino sh -c "cd '$PWD'; alembic upgrade head"
