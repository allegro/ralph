# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.admin import RalphAdmin, register
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.supports.models import Support, SupportType


@register(Support)
class SupportAdmin(PermissionAdminMixin, RalphAdmin):

    """Support model admin class."""

    search_fields = [
        'name', 'serial_no', 'contract_id', 'description', 'additional_notes'
    ]
    list_filter = ['support_type']
    date_hierarchy = 'created'
    flist_display = [
        'support_type', 'contract_id', 'name', 'serial_no', 'date_from',
        'date_to', 'created', 'additional_notes', 'description'
    ]
    list_select_related = ['support_type']


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):
    pass
