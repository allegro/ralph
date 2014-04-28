#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from fabric import colors
from fabric.api import cd, env, local, run
from fabric.context_managers import hide
from fabric.decorators import hosts, parallel
from fabric.operations import put
from fabric.utils import abort

import fabconf


env.user = 'ralph'


def _reset_title():
    with hide('running'):
        local('echo "\\033]0;$HOSTNAME\\007"')


def _git(command):
    if command == 'pull':
        local(
            'git push ssh://ralph@{}{} master:master'.format(
                env.host, fabconf.PROJECT_DIR,
            ),
        )
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
