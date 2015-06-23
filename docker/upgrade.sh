#!/bin/bash
set -e
cd $RALPH_DIR

make docs
gulp

$RALPH_EXEC migrate --noinput
$RALPH_EXEC collectstatic -l --noinput
$RALPH_EXEC sitetreeload
$RALPH_EXEC sitetree_resync_apps
