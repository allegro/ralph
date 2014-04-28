# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.inclusion_tag('cmdb/cmdb_table.html')
def cmdb_table(table_header, table_body, url_query):
    return locals()
