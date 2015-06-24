#!/bin/bash
set -e

cd $RALPH_DIR
ln -s /usr/bin/nodejs /usr/bin/node  # fix node.js on ubuntu
npm install -g bower
npm install --skip-installed
