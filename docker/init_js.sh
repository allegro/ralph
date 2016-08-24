#!/bin/bash
set -e

export NVM_DIR="/root/.nvm"
source $NVM_DIR/nvm.sh
cd $RALPH_DIR
$RALPH_DIR/node_modules/.bin/gulp build
