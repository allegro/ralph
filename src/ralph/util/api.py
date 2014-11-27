#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User


def _get_api_key(request):
    try:
        return (
            request.REQUEST.get('api_key')
            or request.META.get('HTTP_AUTHORIZATION').split(' ')[-1]
        )
    except AttributeError:
        return False


def get_user(request):
    username = request.REQUEST.get('username')
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            api_key = _get_api_key(request)
            user = User.objects.get(api_key__key=api_key)
        except User.DoesNotExist:
            user = None
    return user


def is_authenticated(user, request):
    api_key = _get_api_key(request)
    if user and user.api_key.key == api_key:
        is_authenticated = True
    else:
        is_authenticated = False
    return is_authenticated
