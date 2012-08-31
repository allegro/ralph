#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User


def is_authenticated(request):
    username = request.GET.get('username')
    api_key = request.GET.get('api_key')
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    return user and user.api_key.key == api_key
