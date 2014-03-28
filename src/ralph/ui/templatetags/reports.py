# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.inclusion_tag('ui/templatetags/wait_for_results.html')
def wait_for_results(autoreload=True, reload_frequency=60):
    return {
        'autoreload': autoreload,
        'reload_frequency': reload_frequency * 1000,
    }


@register.simple_tag
def links(items):
    return ', '.join(
        ('<a href="{0}">{1}</a>'.format(item.url, item.id) for item in items)
    )
