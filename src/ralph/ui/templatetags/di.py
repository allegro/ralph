# -*- coding: utf-8 -*-
"""Tags for dependency injection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template

from ralph.util.di import get_extra_data

register = template.Library()


@register.simple_tag
def extra_inclusion(name, *args, **kwargs):
    return get_extra_data(name, *args, **kwargs) or ''
