#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from fabric import colors
from fabric.api import cd, get, env, local, run
from fabric.context_managers import hide
from fabric.decorators import hosts, parallel
from fabric.operations import put
from fabric.utils import abort

import fabconf

env.user = 'ralph'

def _reset_title():
    with hide('running'):
        local('echo "\\033]0;$HOSTNAME\\007"')

def _git (command):
    if command == 'pull':
        local('git push ssh://ralph@{}{} master:master'
                ''.format(env.host, fabconf.PROJECT_DIR))
        with cd(fabconf.PROJECT_DIR):
            run('git checkout -f'.format(command))
            if hasattr(fabconf, 'PIP_INSTALL'):
                run(fabconf.PIP_INSTALL(env))
            else:
                run('pip install -e .')
    elif command == 'status':
        with cd(fabconf.PROJECT_DIR):
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
    with cd(fabconf.PROJECT_DIR):
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

def _patch(path):
    filename = os.path.split(path)[1] or path
    put(path, '/tmp/' + filename)
    with cd(fabconf.SITE_PACKAGES_DIR):
        run('patch -p2 < /tmp/' + filename)

@hosts(*fabconf.PROD_HOSTS)
def patch_prod(command):
    _patch(command)

@parallel
@hosts(*fabconf.PROD_HOSTS)
def ppatch_prod(command):
    _patch(command)

@hosts(*fabconf.DEV_HOSTS)
def patch_dev(command):
    _patch(command)

@parallel
@hosts(*fabconf.DEV_HOSTS)
def ppatch_dev(command):
    _patch(command)
