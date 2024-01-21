#!/bin/bash
set -e
cd /var/local/ralph
npm install
./node_modules/.bin/gulp
