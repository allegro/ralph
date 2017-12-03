#!/bin/bash
set -e


apt-get install -y --force-yes \
    build-essential \
    git \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-dev \
    mysql-client \
    python3 \
    python3-dev \
    python3-setuptools \
    wget
easy_install3 pip
pip3 install --upgrade setuptools
