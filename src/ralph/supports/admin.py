# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.supports.models import Support, SupportType


class BaseObjectSupportView(RalphDetailViewAdmin):
    icon = 'laptop'
    name = 'base-object-assignments'
    label = _('Assignments')
    url_name = 'assignments'

    class BaseObjectSupportInline(RalphTabularInline):
        model = Support.base_objects.through
        raw_id_fields = ('baseobject',)
        extra = 1
        verbose_name = _('Base object support')

    inlines = [BaseObjectSupportInline]


@register(Support)
class SupportAdmin(PermissionAdminMixin, RalphAdmin):

    """Support model admin class."""

    change_views = [BaseObjectSupportView]
    search_fields = [
        'name', 'serial_no', 'contract_id', 'description', 'remarks'
    ]
    list_filter = ['support_type']
    date_hierarchy = 'created'
    list_display = [
        'support_type', 'contract_id', 'name', 'serial_no', 'date_from',
        'date_to', 'created', 'remarks', 'description'
    ]
    list_select_related = ['support_type']
    resource_class = resources.SupportResource
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
                'supplier', 'invoice_date', 'invoice_no', 'period_in_months',
            )
        }),
    )


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):

    resource_class = resources.SupportTypeResource
