#!/bin/bash

sudo apt-get install -y nodejs npm
sudo npm install -g bower
cd ~/src/ralph
sudo ln -s /usr/bin/nodejs /usr/bin/node
sudo npm install
gulp
