#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import Iterable

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


def getattr_dunder(obj, attr):
    """Gets attribute of object. Works recursively
    if attr contains double underscores."""

    first, dunder, rest = attr.partition('__')
    value = getattr(obj, first)
    if rest:
        return getattr_dunder(value, rest)
    return value


class Getter(Iterable):
    """A generic tool for various internal apis, that yields dicts with
    given fields from a collection."""

    filters = {}

    def get_queryset(self):
        """Returns a queryset for this collection."""
        return self.Model.objects.filter(**self.filters)

    def format_item(self, item):
        """Formats a single item."""
        ret = {}
        for field in self.fields:
            if isinstance(field, basestring):
                ret[field] = getattr_dunder(item, field)
            else:
                name, get_function = field
                if isinstance(get_function, basestring):
                    ret[name] = getattr_dunder(item, get_function)
                else:
                    ret[name] = get_function(item)
        return ret

    def __iter__(self):
        for item in self.get_queryset():
            yield self.format_item(item)
