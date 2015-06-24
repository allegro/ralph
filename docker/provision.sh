#!/bin/bash
set -e

apt-get update

apt-get install -y \
    git \
    libmysqlclient-dev \
    mysql-client \
    python-dev \
    python-virtualenv \
    python3.4 \
    python3.4-dev \
    nodejs \
    npm
