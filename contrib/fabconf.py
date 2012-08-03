#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


PROD_HOSTS = ('ralph01.prod', 'ralph04.prod')
DEV_HOSTS = ('ralph02.dev', 'ralph03.dev')

PROJECT_DIR = '/home/ralph/project'
SITE_PACKAGES_DIR = '/home/ralph/lib/python2.7/site-packages'

def PIP_INSTALL(env):
    if env.host.endswith('.dev'):
        return 'pip install --proxy=proxy.dev:8000 -e .'
    return 'pip install -e .'
