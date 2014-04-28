from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape as esc


from ralph.util import presentation


register = template.Library()


@register.filter(name="icon")
def icon_filter(name):
    return mark_safe('<i class="fugue-icon %s"></i>' % esc(name))


@register.filter
def device_icon(device):
    return icon_filter(presentation.get_device_icon(device))


@register.filter
def venture_icon(venture):
    return icon_filter(presentation.get_venture_icon(venture))


@register.filter
def owner_icon(owner):
    return icon_filter(presentation.get_owner_icon(owner))


@register.filter
def address_icon(ip):
    if not ip:
        return ''
    if ip.is_buried:
        icon_name = 'fugue-headstone'
    elif ip.is_management:
        icon_name = 'fugue-system-monitor-network'
    else:
        icon_name = 'fugue-network-ip'
    return icon_filter(icon_name)


@register.filter
def field_icon(field, form):
    icon_name = form.icons.get(field.name, 'fugue-property')
    return icon_filter(icon_name)


@register.filter
def alert_icon(alert_type):
    icon_name = {
        'info': 'fugue-information',
        'error': 'fugue-exclamation-red',
        'warning': 'fugue-exclamation',
        'success': 'fugue-tick',
    }.get(alert_type, 'fugue-sticky-note')
    return icon_filter(icon_name)


@register.filter
def device_model_type_icon(model_type_id):
    icon_name = presentation.DEVICE_ICONS.get(
        model_type_id, 'fugue-wooden-box')
    return icon_filter(icon_name)


@register.filter
def component_model_type_icon(model_type_id):
    icon_name = presentation.COMPONENT_ICONS.get(model_type_id, 'fugue-box')
    return icon_filter(icon_name)


@register.filter
def network_icon(network):
    return icon_filter(presentation.get_network_icon(network))


@register.simple_tag
def icon(icon_name):
    return icon_filter(icon_name)
