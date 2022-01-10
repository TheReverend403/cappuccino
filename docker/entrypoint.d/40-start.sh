#!/bin/sh
exec sudo -E -u cappuccino sh -c "cd '$PWD'; $@"
