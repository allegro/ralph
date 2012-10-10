#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

try:
    USE_CELERY = settings.ISSUETRACKERS['default']['USE_CELERY']
    # additional check - if null issue tracker, ALWAYS forbid celery
    if settings.ISSUETRACKERS['default']['ENGINE'] == '':
        USE_CELERY = False
except KeyError:
    USE_CELERY = False


def getfunc(method):
    """ When debugging use direct method, in production deffer for celery  """
    if USE_CELERY:
        return method.delay
    else:
        return method

