#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User


def get_user(request):
    username = request.REQUEST.get('username')
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    return user


def is_authenticated(user, request):
    api_key = request.REQUEST.get('api_key')
    if user and user.api_key.key == api_key:
        is_authenticated = True
    else:
        is_authenticated = False
    return is_authenticated
