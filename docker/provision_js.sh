#!/bin/bash
set -e

cd $RALPH_DIR
wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.31.4/install.sh | bash
export NVM_DIR="/root/.nvm"
source ~/.bashrc
source $NVM_DIR/nvm.sh
nvm install node
npm install -g bower
npm install --skip-installed
npm install gulp
