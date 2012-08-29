#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals



def getfunc(method):
    """ Wrapper for calling methods - via celery or directly  """
    celery = False
    if celery:
        return method.delay
    else:
        return method

