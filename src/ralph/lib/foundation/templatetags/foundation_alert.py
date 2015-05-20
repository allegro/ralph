# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template

register = template.Library()


@register.inclusion_tag('foundation_alert/alert.html')
def alert(message, css_class='success', is_close=True):
    """Render foundation alert box."""
    return {'message': message, 'css_class': css_class, 'is_close': is_close}
