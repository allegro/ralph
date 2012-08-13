from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.conf import settings

register = template.Library()

@register.filter
def currency(number, precision=0):
    try:
        return ('{:,.%df} {}' % precision).format(
                number, settings.CURRENCY).replace(',', ' ')
    except ValueError:
        return number or ''

@register.filter
def key(d, key_name):
    if not d:
        return None
    return d.get(key_name)

@register.filter
def field_value(f):
    return f.field.to_python(f.value())

@register.filter
def range(n, s=0):
    return xrange(s, s + n)

@register.filter
def order_by(query, by):
    return query.order_by(by)


@register.filter
def chassis_order(query):
    return query.order_by('model__type', 'chassis_position', 'position')
