from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.conf import settings

from ajax_select import get_lookup
from ajax_select.fields import AutoCompleteSelectField


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
def deep_field_value(f):
    """Similar to *field_value* filter, but shows related object instead of
    foreign key"""
    field_value = f.field.to_python(f.value())
    if field_value != '' and isinstance(f.field, AutoCompleteSelectField):
        lookup = get_lookup(f.field.channel)
        found = lookup.get_objects([field_value])
        if found:
            field_value = found[0]
    return field_value


@register.filter
def range(n, s=0):
    return xrange(s, s + n)


@register.filter
def order_by(query, by):
    return query.order_by(by)


@register.filter
def chassis_order(query):
    return query.order_by('model__type', 'chassis_position', 'position')


@register.filter
def getfield(d, key_name):
    return d[key_name]


@register.filter
def getfielderrors(d, key_name):
    return d[key_name].errors


@register.filter
def getvalue(d, key_name):
    return d.get(key_name, '')


@register.filter
def split(s, sep=None):
    return s.split(sep)


@register.filter
def max_netmask(num):
    return 32 - (len(bin(num)[2:]) - 1)
