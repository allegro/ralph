#!/bin/bash
set -e
sudo apt-get update

## INSTALL dependencies
# Install MySQL Server in a Non-Interactive mode. NO PASSWORD for root
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server mysql-server libmysqlclient-dev libmysqld-dev

sudo apt-get install -y python-virtualenv python-dev
sudo apt-get install -y python3.4 python3.4-dev
sudo apt-get install -y git


# INSTALL Ralph
virtualenv --clear .
. bin/activate
cd src/ralph/
make install-dev

# CREATE db
./vagrant/provisioning_scripts/init_mysql.sh

# final setups
cat /home/vagrant/src/ralph/vagrant/provisioning_scripts/profile_extensions >> /home/vagrant/.profile
