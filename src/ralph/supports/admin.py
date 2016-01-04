# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.supports.models import BaseObjectsSupport, Support, SupportType


class BaseObjectSupportView(RalphDetailViewAdmin):
    icon = 'laptop'
    name = 'base-object-assignments'
    label = _('Assignments')
    url_name = 'assignments'

    class BaseObjectSupportInline(RalphTabularInline):
        model = BaseObjectsSupport
        raw_id_fields = ('baseobject',)
        extra = 1
        verbose_name = _('assignments')
        verbose_name_plural = _('Assignments')
        fk_name = 'support'

    inlines = [BaseObjectSupportInline]


@register(Support)
class SupportAdmin(
    AttachmentsMixin,
    BulkEditChangeListMixin,
    PermissionAdminMixin,
    RalphAdmin
):

    """Support model admin class."""

    change_views = [BaseObjectSupportView]
    actions = ['bulk_edit_action']
    search_fields = [
        'name', 'serial_no', 'contract_id', 'description', 'remarks'
    ]
    list_filter = [
        'contract_id', 'name', 'serial_no', 'price', 'remarks', 'description',
        'support_type', 'budget_info', 'date_from', 'date_to', 'property_of'
    ]
    date_hierarchy = 'created'
    list_display = [
        'support_type', 'contract_id', 'name', 'serial_no', 'date_from',
        'date_to', 'created', 'remarks', 'description'
    ]
    bulk_edit_list = [
        'status', 'asset_type', 'contract_id', 'description', 'price',
        'date_from', 'date_to', 'escalation_path', 'contract_terms',
        'sla_type', 'producer', 'supplier', 'serial_no', 'invoice_no',
        'invoice_date', 'period_in_months', 'property_of', 'budget_info',
        'support_type'
    ]
    list_select_related = ['support_type']
    resource_class = resources.SupportResource
    raw_id_fields = ['budget_info', 'region', 'support_type']
    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'support_type', 'name', 'status', 'producer', 'description',
                'date_from', 'date_to', 'serial_no', 'escalation_path',
                'region', 'remarks',
            )
        }),
        (_('Contract info'), {
            'fields': (
                'contract_id', 'contract_terms', 'sla_type', 'price',
                'supplier', 'invoice_date', 'invoice_no', 'budget_info',
                'period_in_months', 'property_of',
            )
        }),
    )


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):

    resource_class = resources.SupportTypeResource
    search_fields = ['name']
