# Ralph-NG

**This is redesigned and rewrite from scratch Ralph version under heavy development. NOT FOR PRODUCTION USE RIGHT NOW**

Ralph is full-featured Asset Management, DCIM and CMDB system for data center and back office.

Features:

* auto-discover existing hardware
* keep track of assets purchases and their life cycle
* generate flexible and accurate cost reports
* integrate with change management process using JIRA integration

It is an Open Source project provided on Apache v2.0 License.

[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/allegro/ralph?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Stories in Ready](https://badge.waffle.io/allegro/ralph.png?label=ready&title=Ready)](http://waffle.io/allegro/ralph)


Installation
============

Vagrant environment
-------------------

It's recommended to use Vagrant for development. Install Vagrant first (https://www.vagrantup.com/). To set-up Ralph environment run:

    cd vagrant
    vagrant up

Then ssh to virtual system:

    vagrant ssh


Regular environmnent
--------------------

To install development version of ralph run:

    pip install -r requirements/dev.txt


Running
=======

Virtualenv is automatically activated. To start (development) server run:

    dev_ralph runserver_plus 0.0.0.0:8000

Ralph is available at `127.0.0.1:8000`.


