#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

def trottle_hook():
    '''If cache backend is DummyCache, TastyPie returns error'''
    cache = getattr(settings, 'CACHES', {})
    cache_default = cache.get('default')
    if cache_default and cache_default['BACKEND'].endswith('DummyCache'):
        return False
    return True
