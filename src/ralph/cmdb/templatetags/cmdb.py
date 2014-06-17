# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import template

from ralph.cmdb.models_ci import CIOwnershipType
from ralph.ui.templatetags.icons import icon_filter


register = template.Library()


OWNER_ICONS = {
    CIOwnershipType.technical.id: 'fugue-user-worker',
    CIOwnershipType.business.id: 'fugue-user-business',
    None: 'fugue-user-nude',
}


@register.inclusion_tag('cmdb/cmdb_table.html')
def cmdb_table(table_header, table_body, url_query):
    return locals()


@register.filter
def owner_icon(owner):
    if owner is None:
        icon_class = OWNER_ICONS[None]
    else:
        icon_class = OWNER_ICONS.get(owner.type) or OWNER_ICONS[None]
    return icon_filter(icon_class)
