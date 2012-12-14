#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.template.defaultfilters import stringfilter


no_delimiters = {
    ':': None,
    '.': None,
    '-': None,
    '_': None,
    ' ': None,
}

register = template.Library()


@register.filter
@stringfilter
def delim_none(value):
    return value.translate(no_delimiters)


@register.filter
@stringfilter
def delim_cisco(value):
    m = delim_none(value)
    return '.'.join('%s%s%s%s' % c for c in zip(*[m[i::4] for i in range(4)]))


@register.filter
@stringfilter
def delim_colon(value):
    m = delim_none(value)
    return ':'.join('%s%s' % c for c in zip(*[m[i::2] for i in range(2)]))
