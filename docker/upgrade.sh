#!/bin/bash
set -e
RALPH_EXEC=/usr/local/bin/ralph
cd $RALPH_DIR
make docs
$RALPH_EXEC migrate --noinput
$RALPH_EXEC collectstatic -l --noinput
