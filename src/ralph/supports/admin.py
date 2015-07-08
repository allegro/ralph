# -*- coding: utf-8 -*-
from ralph.admin import RalphAdmin, register
from ralph.data_importer import resources
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
    list_display = [
        'support_type', 'contract_id', 'name', 'serial_no', 'date_from',
        'date_to', 'created', 'additional_notes', 'description'
    ]
    list_select_related = ['support_type']
    resource_class = resources.SupportResource


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):

    resource_class = resources.SupportTypeResource
