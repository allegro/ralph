# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.licences.models import Licence, LicenceType, SoftwareCategory


@register(Licence)
class LicenceAdmin(PermissionAdminMixin, RalphAdmin):

    """Licence admin class."""

    search_fields = ['niw', 'sn', 'license_details', 'remarks']
    list_filter = ['licence_type']
    date_hierarchy = 'created'
    list_display = [
        'niw', 'licence_type', 'software_category', 'number_bought',
        'invoice_date', 'invoice_no', 'valid_thru', 'created'
    ]
    list_select_related = ['licence_type', 'software_category']
    raw_id_fields = ['software_category', 'manufacturer']

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'licence_type', 'manufacturer', 'software_category',
                'niw', 'sn', 'valid_thru', 'license_details',
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
class LicenceTypeAdmin(PermissionAdminMixin, RalphAdmin):
    pass


@register(SoftwareCategory)
class SoftwareCategoryAdmin(PermissionAdminMixin, RalphAdmin):
    pass
