#!/bin/bash
set -e
cd /var/local/ralph
uv sync --locked
if [[ ! -d src/ralph/static/vendor || ! -d src/ralph/static/css ]]; then
  /opt/local/rebuild-local-dev-statics.sh
else
  echo "Statics found. Not attempting to recreate them"
fi
uv run ralph runserver 0.0.0.0:8000
