# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.inclusion_tag('foundation_form/form_label.html')
def label(field):
    """Render foundation label."""
    return {'field': field}


@register.inclusion_tag('foundation_form/form_field.html')
def field(field):
    """Render foundation field."""
    return {'field': field, 'show_label': True}


@register.inclusion_tag('foundation_form/form_field.html')
def field_alone(field):
    """Render foundation field without label."""
    return {'field': field, 'show_label': False}


@register.inclusion_tag('foundation_form/form_errors.html')
def errors(form):
    """Render non field errors for a form."""
    return {'form': form}
