#!/bin/bash
set -e
for RALPH_ENV in $@
do
    DJANGO_SETTINGS_MODULE=ralph.settings.$RALPH_ENV ralph;
done
