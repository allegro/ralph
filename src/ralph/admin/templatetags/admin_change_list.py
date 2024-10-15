from django.contrib.admin.views.main import PAGE_VAR
from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = Library()

DOT = "."
DOTS = DOT * 3


@register.simple_tag
def admin_paginator_number(cl, i):
    """
    Generates an individual page index link in a paginated list.

    Wraps every entry in <li> tag comparing to regular Django pagination.
    """
    if i == DOT:
        return mark_safe("<li>{}</li>".format(DOTS))
    elif i == cl.page_num:
        return format_html('<li class="current"><a href="#">{}</a></li> ', i + 1)
    else:
        return format_html(
            '<li><a href="{}">{}</a></li> ', cl.get_query_string({PAGE_VAR: i}), i + 1
        )
