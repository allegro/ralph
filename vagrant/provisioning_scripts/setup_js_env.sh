#!/bin/bash
set -e

sudo apt-get update
sudo apt-get install -y \
    nodejs \
    npm

# node-debian bug walkaround: debian `node` is called `nodejs`, but npm requires to have `node`
sudo ln -s /usr/bin/nodejs /usr/bin/node

cd ~/src/ralph
# update npm
sudo npm install -g npm

npm install
gulp
