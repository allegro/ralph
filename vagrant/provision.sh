#!/bin/bash
set -e
sudo apt-get update

## INSTALL dependencies
# Install MySQL Server in a Non-Interactive mode. NO PASSWORD for root
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    libldap2-dev \
    libmysqlclient-dev \
    libmysqld-dev \
    libsasl2-dev \
    mysql-server-5.6 \
    python3.4 \
    python3.4-dev \
    redis-server

# INSTALL Ralph in virtualenv
# create virtualenv without pip - ubuntu 14.04 comes with broken Python3.4's pip
# see http://askubuntu.com/questions/488529/pyvenv-3-4-error-returned-non-zero-exit-status-1
# and https://bugs.launchpad.net/ubuntu/+source/python3.4/+bug/1290847
pyvenv-3.4 --without-pip .
. bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
cd src/ralph/
make install-dev

cat /home/vagrant/src/ralph/vagrant/provisioning_scripts/profile_extensions >> /home/vagrant/.profile
source /home/vagrant/.profile

# create local settings file
SETTINGS_LOCAL_PATH=/home/vagrant/src/ralph/src/ralph/settings/local.py
if [ ! -f $SETTINGS_LOCAL_PATH ]; then
    echo "from ralph.settings.dev import *  # noqa" > $SETTINGS_LOCAL_PATH
fi

# CREATE db
./vagrant/provisioning_scripts/init_mysql.sh

# final setups
./vagrant/provisioning_scripts/setup_js_env.sh
