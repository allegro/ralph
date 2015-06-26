#!/bin/bash
set -e

# wait for db init
sleep 15

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR

./upgrade.sh

$RALPH_EXEC createsuperuser --noinput --username ralph --email ralph@allegrogroup.com
python3 $RALPH_DIR/docker/createsuperuser.py
