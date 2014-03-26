from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.filter
def query_page(query, page):
    query = query.copy()
    if page is not None and page not in ('1', 1):
        query['page'] = page
    else:
        try:
            del query['page']
        except KeyError:
            pass
    return query.urlencode()


@register.filter
def query_sort(query, sort):
    query = query.copy()
    if sort:
        query['sort'] = sort
    else:
        try:
            del query['sort']
        except KeyError:
            pass
    return query.urlencode()


@register.filter
def query_sort_desc(query, sort):
    query = query.copy()
    query['sort'] = '-' + sort
    return query.urlencode()


@register.filter
def query_export(query, export):
    query = query.copy()
    if export:
        query['export'] = export
    else:
        try:
            del query['export']
        except KeyError:
            pass
    return query.urlencode()
