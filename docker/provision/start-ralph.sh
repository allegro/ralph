#!/bin/bash

set -ue


/opt/ralph/ralph-core/bin/gunicorn --daemon -c "${RALPH_LOCAL_DIR}/gunicorn.ini" ralph.wsgi

"${RALPH_LOCAL_DIR}/wait-for-it.sh" "${GUNICORN_BIND}" --timeout=30 --strict -- echo "Gunicorn is up"

tail -f /var/log/ralph/ralph.log /var/log/ralph/gunicorn.error.log
