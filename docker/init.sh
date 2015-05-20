#!/bin/bash
set -e

# wait for db init
sleep 15

ralph migrate

ralph createsuperuser --noinput --username ralph --email ralph@allegrogroup.com
python $RALPH_DIR/docker/createsuperuser.py
