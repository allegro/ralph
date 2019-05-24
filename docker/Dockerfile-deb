FROM ubuntu:bionic

LABEL maintainer="Allegro.pl Sp. z o.o. opensource@allegro.pl"
LABEL authors="Allegro.pl Sp. z o.o. and Contributors opensource@allegro.pl"
LABEL description="Helper image to build deb package for Ralph."

ARG GIT_USER_NAME='root'
ARG GIT_USER_EMAIL='root@localhost'

ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash
ENV TERM=xterm
ENV EDITOR=nano
ENV RALPH_DIR=/opt/ralph

RUN apt-get update && \
    apt-get -y install build-essential debhelper devscripts equivs dh-virtualenv \
    git libmysqlclient-dev python3 python3-dev libffi-dev nodejs npm git-buildpackage \
    vim-tiny && \
    rm -rf /var/lib/apt/lists/* && \
    git config --global user.name "$GIT_USER_NAME" && \
    git config --global user.email "$GIT_USER_EMAIL"

COPY . $RALPH_DIR

WORKDIR $RALPH_DIR
ENTRYPOINT ["make", "-f", "Makefile.docker"]
