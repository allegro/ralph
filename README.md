# Ralph-NG

Ralph is full-featured Asset Management, DCIM and CMDB system for data center and back office.

Features:

* keep track of assets purchases and their life cycle
* generate flexible and accurate cost reports
* integrate with change management process using JIRA integration

It is an Open Source project provided on Apache v2.0 License.

[![Gitter](https://img.shields.io/gitter/room/gitterHQ/gitter.svg)](https://gitter.im/allegro/ralph?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/allegro/ralph.svg)](https://travis-ci.org/allegro/ralph)
[![Coverage Status](https://coveralls.io/repos/allegro/ralph/badge.svg?branch=ng&service=github)](https://coveralls.io/github/allegro/ralph?branch=ng)
[![Code Health](https://landscape.io/github/allegro/ralph/ng/landscape.svg?style=flat)](https://landscape.io/github/allegro/ralph/ng)

# Live demo:

http://ralph-demo.allegro.tech/

* login: ralph
* password: ralph

# Installation

## Debian package(recommended)

Visit our documentation on [readthedocs.org](http://ralph-ng.readthedocs.org) for more details.

## Docker installation (with [docker-compose](https://docs.docker.com/compose/))

#### Build and run services

    docker-compose up -d

Ralph should be accessible at ``http://127.0.0.1`` or ``http://your.server.ip.addr``

#### First run

    docker-compose exec ralph ralph migrate --noinput
    docker-compose exec ralph ralph collectstatic --noinput
    docker-compose exec ralph ralph createsuperuser
    docker-compose exec ralph ralph sitetree_resync_apps

#### Upgrade DB and static files

    docker-compose exec ralph ralph migrate --noinput
    docker-compose exec ralph ralph collectstatic --noinput

## Developer installation

It's recommended to use Vagrant for development. Install Vagrant first (https://www.vagrantup.com/). To set-up Ralph environment run:

    cd vagrant
    vagrant up

Then ssh to virtual system:

    vagrant ssh

Virtualenv is activated for you automatically.


## Manual installation

Make sure you created virtualenv in which you will install ralph.
If you want to install it in production, after cloning ralph repository, and activating virtualenv just make:

    make install
    ralph migrate
    make menu

Or if you want to run in debug mode for detailed error messages and debug toolbar:

    make install-dev
    dev_ralph migrate
    make menu

will install it for you as well.

## Running

Make sure virtualenv is activated. To start server in debug mode:

    make run

or if you don't want the debug output

    ralph runserver_plus 0.0.0.0:8000


Ralph is available at `127.0.0.1:8000`.


## Documentation
Visit our documentation on [readthedocs.org](http://ralph-ng.readthedocs.org)

## Getting help

Ralph community will answer your questions on a chat: [![Gitter](https://img.shields.io/gitter/room/gitterHQ/gitter.svg)](https://gitter.im/allegro/ralph?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Scrum Board

[![Stories in Ready](https://badge.waffle.io/allegro/ralph.png?label=ready&title=Ready)](http://waffle.io/allegro/ralph)

[![Throughput Graph](https://graphs.waffle.io/allegro/ralph/throughput.svg)](https://waffle.io/allegro/ralph/metrics)
