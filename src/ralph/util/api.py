#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User


class NoApiKeyError(Exception):
    pass


def _get_api_key(request):
    try:
        api_key = (
            request.REQUEST.get('api_key') or
            request.META.get('HTTP_AUTHORIZATION').split(' ')[-1]
        )
    except AttributeError:
        api_key = ''

    if not api_key:
        raise NoApiKeyError()
    return api_key


def get_user(request):
    username = request.REQUEST.get('username')
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        api_key = _get_api_key(request)
        return User.objects.get(api_key__key=api_key)
