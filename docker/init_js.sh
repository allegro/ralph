#!/bin/bash
set -e

cd $RALPH_DIR
$RALPH_DIR/node_modules/.bin/gulp
$RALPH_DIR/node_modules/.bin/gulp polymer-prod
