# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.admin.views.main import PAGE_VAR
from django.template import Library
from django.utils.html import format_html


register = Library()

DOT = '.'


@register.simple_tag
def admin_paginator_number(cl, i):
    """
    Generates an individual page index link in a paginated list.
    """
    if i == DOT:
        return '... '
    elif i == cl.page_num:
        return format_html(
            '<li class="current"><a href="#">{}</a></li> ', i + 1)
    else:
        return format_html(
            '<li><a href="{}">{}</a></li> ',
            cl.get_query_string({PAGE_VAR: i}),
            i + 1
        )
