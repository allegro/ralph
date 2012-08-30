#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings


def getfunc(method):
    """ When debugging use direct method, in production deffer for celery  """
    celery = not settings.DEBUG
    if celery:
        return method.delay
    else:
        return method

