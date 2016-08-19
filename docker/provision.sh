#!/bin/bash
set -e

apt-get update

apt-get install -y --force-yes \
    git \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-dev \
    mysql-client \
    python3.4 \
    python3.4-dev \
    python3-pip \
    wget \
    vim
