# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.assets.invoice_report import InvoiceReportMixin
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)


class BaseObjectLicenceView(RalphDetailViewAdmin):
    icon = 'laptop'
    name = 'base-object'
    label = _('Assignments')
    url_name = 'assignments'

    class BaseObjectLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ('base_object',)
        extra = 1
        verbose_name = _('assignments')
        verbose_name_plural = _('Assignments')
        fk_name = 'licence'

    inlines = [BaseObjectLicenceInline]


class LicenceUserView(RalphDetailViewAdmin):
    icon = 'user'
    name = 'users'
    label = _('Assigned to users')
    url_name = 'assigned-to-users'

    class LicenceUserInline(RalphTabularInline):
        model = LicenceUser
        raw_id_fields = ('user',)
        extra = 1

    inlines = [LicenceUserInline]


@register(Licence)
class LicenceAdmin(
    PermissionAdminMixin,
    AttachmentsMixin,
    InvoiceReportMixin,
    RalphAdmin
):

    """Licence admin class."""
    change_views = [
        BaseObjectLicenceView,
        LicenceUserView,
    ]
    search_fields = ['niw', 'sn', 'license_details', 'remarks']
    list_filter = [
        'niw', 'sn', 'remarks', 'software', 'property_of',
        'licence_type', 'valid_thru', 'order_no', 'invoice_no', 'invoice_date',
        'budget_info', 'manufacturer', 'region', 'office_infrastructure'
    ]
    date_hierarchy = 'created'
    list_display = [
        'niw', 'licence_type', 'software', 'number_bought',
        'invoice_date', 'invoice_no', 'valid_thru', 'created', 'region'
    ]
    list_select_related = ['licence_type', 'software', 'region']
    raw_id_fields = [
        'software', 'manufacturer', 'budget_info', 'office_infrastructure'
    ]
    resource_class = resources.LicenceResource
    _invoice_report_name = 'invoice-licence'
    _invoice_report_select_related = ['software', 'manufacturer']
    _invoice_report_item_fields = [
        'software', 'manufacturer', 'software__get_asset_type_display', 'niw',
        'sn', 'price', 'created'
    ]

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'licence_type', 'manufacturer', 'software',
                'niw', 'sn', 'valid_thru', 'license_details', 'region',
                'remarks'
            )
        }),
        (_('Financial info'), {
            'fields': (
                'order_no', 'invoice_no', 'price', 'invoice_date',
                'number_bought', 'accounting_id', 'budget_info', 'provider',
                'office_infrastructure'
            )
        }),
    )


@register(LicenceType)
class LicenceTypeAdmin(
    PermissionAdminMixin,
    RalphAdmin
):

    search_fields = ['name']


@register(Software)
class Software(
    PermissionAdminMixin,
    RalphAdmin
):

    search_fields = ['name']
