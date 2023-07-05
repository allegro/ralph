#!/bin/bash

set -eu

export DJANGO_SETTINGS_MODULE="ralph.settings"

ralph migrate --noinput
ralph sitetree_resync_apps

python3 /opt/local/createsuperuser.py
