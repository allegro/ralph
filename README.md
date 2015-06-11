# Ralph-NG

**This is redesigned and rewritten from scratch Ralph version under heavy development. NOT FOR PRODUCTION USE RIGHT NOW**

Ralph is full-featured Asset Management, DCIM and CMDB system for data center and back office.

Features:

* auto-discover existing hardware
* keep track of assets purchases and their life cycle
* generate flexible and accurate cost reports
* integrate with change management process using JIRA integration

It is an Open Source project provided on Apache v2.0 License.

[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/allegro/ralph?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Code Health](https://landscape.io/github/allegro/ralph/ng/landscape.svg?style=flat)](https://landscape.io/github/allegro/ralph/ng)

## Scrum Board

[![Stories in Ready](https://badge.waffle.io/allegro/ralph.png?label=ready&title=Ready)](http://waffle.io/allegro/ralph)

[![Throughput Graph](https://graphs.waffle.io/allegro/ralph/throughput.svg)](https://waffle.io/allegro/ralph/metrics)

## Installation


## Vagrant environment

It's recommended to use Vagrant for development. Install Vagrant first (https://www.vagrantup.com/). To set-up Ralph environment run:

    cd vagrant
    vagrant up

Then ssh to virtual system:

    vagrant ssh


## Regular environmnent

If you want to install it in production, after cloning ralph repository just make:

    make install
    
Or if you want to run in debug mode for detailed error messages and debug toolbar:

    make install-dev

will install it for you as well.

## Running


Make sure virtualenv is activated. To start server in debug mode:

    make run
    
or if you don't want the debug output

    ralph runserver_plus 0.0.0.0:8000
    

Ralph is available at `127.0.0.1:8000`.


