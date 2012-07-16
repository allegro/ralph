#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from time import sleep

from fabric import colors
from fabric.api import cd, get, env, local, run, settings
from fabric.context_managers import hide
from fabric.decorators import hosts, parallel
from fabric.utils import puts, abort, warn

import fabconf

env.user = 'ralph'

def _reset_title():
    with hide('running'):
        local('echo "\\033]0;$HOSTNAME\\007"')

def _git (command):
    if command == 'pull':
        local('git push ssh://ralph@{}/home/ralph/project master:master'
                ''.format(env.host))
        with cd('/home/ralph/project/'):
            run('git checkout -f'.format(command))
            if hasattr(fabconf, 'PIP_INSTALL'):
                run(fabconf.PIP_INSTALL(env))
            else:
                run('pip install -e .')
    elif command == 'status':
        with cd('/home/ralph/project/'):
            run('git {}'.format(command))
    else:
        abort(colors.red('Invalid remote git command.'))
    _reset_title()

@hosts(*fabconf.PROD_HOSTS)
def git_prod(command):
    _git(command)

@parallel
@hosts(*fabconf.PROD_HOSTS)
def pgit_prod(command):
    _git(command)

@hosts(*fabconf.DEV_HOSTS)
def git_dev(command):
    _git(command)

@parallel
@hosts(*fabconf.DEV_HOSTS)
def pgit_dev(command):
    _git(command)

def _celery(command):
    if command == 'tail':
        run('tail /var/log/celery/worker.log')
        _reset_title()
        return
    elif command == 'fetchlogs':
        get('/var/log/celery/worker.log', 'logs/%(host)s/worker.log')
        _reset_title()
        return
    if command not in ('start', 'stop', 'restart', 'kill', 'status'):
        abort(colors.red('Invalid celeryd command.'))
    with cd('/home/ralph/project/src/ralph'):
        run('/etc/init.d/celeryd {}'.format(command))
    _reset_title()

@hosts(*fabconf.PROD_HOSTS)
def celery_prod(command):
    _celery(command)

@parallel
@hosts(*fabconf.PROD_HOSTS)
def pcelery_prod(command):
    _celery(command)

@hosts(*fabconf.DEV_HOSTS)
def celery_dev(command):
    _celery(command)

@parallel
@hosts(*fabconf.DEV_HOSTS)
def pcelery_dev(command):
    _celery(command)
