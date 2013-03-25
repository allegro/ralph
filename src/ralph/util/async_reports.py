# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from hashlib import md5

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, get_cache


def get_cache_key(base_name, *args, **kwargs):
    params_str = '%s_%s_%s' % (
        base_name,
        ','.join([str(arg) for arg in args]),
        ','.join(
            ['%s:%s' % (
                key,
                kwargs.get(key, ''),
            ) for key in sorted(kwargs.keys())],
        ),
    )
    md5_hash = md5(params_str)
    return md5_hash.hexdigest()


def async_report_provider(timeout, cache_alias=DEFAULT_CACHE_ALIAS):
    def _async_report_provider(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache = get_cache(
                cache_alias
                if cache_alias in settings.CACHES else DEFAULT_CACHE_ALIAS,
            )
            cache.set(
                get_cache_key(func.func_name, *args, **kwargs),
                result,
                timeout,
            )
            return result
        wrapper.func_dict.update({
            'async_report_results_expiration': timeout,
            'async_report_cache_alias': cache_alias if (
                cache_alias in settings.CACHES
            ) else DEFAULT_CACHE_ALIAS
        })
        wrapper.__name__ = func.__name__
        wrapper.__module__ = func.__module__
        return wrapper
    return _async_report_provider
