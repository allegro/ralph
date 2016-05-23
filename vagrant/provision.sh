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
    make \
    mysql-server-5.6 \
    python3.4 \
    python3.4-dev \
    python3.4-venv \
    python3-pip \
    redis-server

pip3 install virtualenv
virtualenv .
. bin/activate

curl https://bootstrap.pypa.io/get-pip.py | python

cd src/ralph/
make install-dev

cat ~/src/ralph/vagrant/provisioning_scripts/profile_extensions >> ~/.profile
source ~/.profile

# create local settings file
SETTINGS_LOCAL_PATH=~/src/ralph/src/ralph/settings/local.py
if [ ! -f $SETTINGS_LOCAL_PATH ]; then
    echo "from ralph.settings.dev import *  # noqa" > $SETTINGS_LOCAL_PATH
fi

# CREATE db
./vagrant/provisioning_scripts/init_mysql.sh

# final setups
./vagrant/provisioning_scripts/setup_js_env.sh

# install LibreOffice and dependencies
./vagrant/provisioning_scripts/libre_office.sh
