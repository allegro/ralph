#!/bin/bash
set -e
cd $RALPH_DIR

make docs

$RALPH_EXEC migrate --noinput
$RALPH_EXEC collectstatic --noinput

make menu
