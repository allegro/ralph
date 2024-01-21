#!/bin/bash
set -e
pip3 install -r /var/local/ralph/requirements/dev.txt
cd /var/local/ralph
if [[ ! -d src/ralph/static/vendor || ! -d src/ralph/static/css ]]; then
  /opt/local/rebuild-local-dev-statics.sh
else
  echo "Statics found. Not attempting to recreate them"
fi
make run
