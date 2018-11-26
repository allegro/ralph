#!/bin/bash

/opt/ralph/ralph-core/bin/gunicorn --daemon -c "${RALPH_LOCAL_DIR}/gunicorn.ini" ralph.wsgi

while [ ! -f /var/log/ralph/ralph.log ] || [ ! -f /var/log/ralph/gunicorn.error.log ]
do
    sleep 1
done

tail -f /var/log/ralph/ralph.log /var/log/ralph/gunicorn.error.log
