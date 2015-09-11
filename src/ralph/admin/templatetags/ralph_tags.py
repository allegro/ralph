# -*- coding: utf-8 -*-
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.contrib.admin.views.main import SEARCH_VAR
from django.template import Library

register = Library()


@register.inclusion_tag('admin/templatetags/tabs.html')
def views_tabs(views, name=None, obj=None):
    """
    Render extra views as tabs.
    """
    return {'views': views, 'name': name, 'object': obj}


@register.inclusion_tag('admin/search_form.html', takes_context=True)
def contextual_search_form(context, search_url, search_fields):
    context.update({
        'search_url': search_url,
        'search_fields': search_fields,
        'search_var': SEARCH_VAR,
    })
    return context


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def ralph_submit_row(context):
    """
    Overriding the default templatetag Django and adding
    to it multi_add_url of context.

    Return context.
    """
    ctx = submit_row(context)
    ctx['multi_add_url'] = context.get('multi_add_url', None)
    ctx['multi_add_field'] = context.get('multi_add_field', None)
    return ctx


@register.filter
def get_attr(obj, attr):
    """
    Return class atributte.

    Example:
    {{ obj|get_attr:"my_atribute" }}

    """
    return getattr(obj, attr, None)


@register.filter
def get_verbose_name(obj, name):
    """
    Return verbose name from Django Model.

    Example:
    {{ obj|get_verbose_name:"my_field" }}

    """
    return obj._meta.get_field(name).verbose_name
