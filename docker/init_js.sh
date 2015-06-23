#!/bin/bash
set -e

cd $RALPH_DIR
ln -s /usr/bin/nodejs /usr/bin/node  # fix node.js on ubuntu
npm install
PATH=$PATH:$RALPH_DIR/node_modules/.bin; export PATH
gulp
