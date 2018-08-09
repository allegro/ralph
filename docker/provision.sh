#!/bin/bash
set -eux

export DEBIAN_FRONTEND=noninteractive


apt-get install -y --force-yes \
    build-essential \
    git \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-dev \
    mysql-client \
    python3 \
    python3-dev \
    python3-pip \
    wget

pip3 install --upgrade setuptools
