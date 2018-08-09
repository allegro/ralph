#!/bin/bash
set -e

export NVM_DIR="/root/.nvm"
export bower_registry__search='[https://registry.bower.io]';
source $NVM_DIR/nvm.sh
cd $RALPH_DIR
$RALPH_DIR/node_modules/.bin/gulp build
