#!/bin/bash
set -e
cd $RALPH_DIR

make docs

yes yes | $RALPH_EXEC migrate
$RALPH_EXEC collectstatic --noinput

make menu
