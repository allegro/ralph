# -*- coding: utf-8 -*-
from django.template import Library


register = Library()


@register.inclusion_tag('ralph_admin/templatetags/tabs.html')
def views_tabs(views, name=None):
    """
    Render extra views as tabs.
    """
    return {'views': views, 'name': name}
