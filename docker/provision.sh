#!/bin/bash
set -e

apt-get update

apt-get install -y --force-yes \
    git \
    libffi-dev \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-dev \
    mysql-client \
    python3.4 \
    python3.4-dev \
    python3-setuptools \
    build-essential \
    wget
easy_install3 pip
pip3 install --upgrade setuptools
