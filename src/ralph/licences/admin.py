# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    SoftwareCategory
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
class LicenceAdmin(PermissionAdminMixin, RalphAdmin):

    """Licence admin class."""
    change_views = [
        BaseObjectLicenceView,
        LicenceUserView,
    ]
    search_fields = ['niw', 'sn', 'license_details', 'remarks']
    list_filter = ['licence_type']
    date_hierarchy = 'created'
    list_display = [
        'niw', 'licence_type', 'software_category', 'number_bought',
        'invoice_date', 'invoice_no', 'valid_thru', 'created'
    ]
    list_select_related = ['licence_type', 'software_category']
    raw_id_fields = ['software_category', 'manufacturer']
    resource_class = resources.LicenceResource

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'licence_type', 'manufacturer', 'software_category',
                'niw', 'sn', 'valid_thru', 'license_details', 'region',
                'remarks'
            )
        }),
        (_('Financial info'), {
            'fields': (
                'order_no', 'invoice_no', 'price', 'invoice_date',
                'number_bought', 'accounting_id', 'provider',
            )
        }),
    )


@register(LicenceType)
class LicenceTypeAdmin(
    PermissionAdminMixin,
    RalphAdmin
):

    search_fields = ['name']


@register(SoftwareCategory)
class SoftwareCategoryAdmin(
    PermissionAdminMixin,
    RalphAdmin
):

    search_fields = ['name']
