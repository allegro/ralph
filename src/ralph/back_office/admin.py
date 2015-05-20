# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ralph.back_office.models import (
    BackOfficeAsset,
    Warehouse
)


@admin.register(BackOfficeAsset)
class BackOfficeAssetAdmin(reversion.VersionAdmin):

    """Back Office Asset admin class."""

    list_display = [
        'status', 'barcode', 'purchase_order', 'model', 'user', 'warehouse',
        'sn', 'hostname', 'invoice_date', 'invoice_no'
    ]
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = ['status']
    date_hierarchy = 'created'
    list_select_related = ['model', 'user', 'warehouse']

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'model', 'purchase_order', 'niw', 'barcode', 'sn',
                'warehouse', 'location', 'status', 'task_url',
                'loan_end_date', 'hostname', 'service_env',
                'production_year', 'production_use_date',
                'required_support', 'remarks'
            )
        }),
        (_('Financial Info'), {
            'fields': (
                'order_no', 'invoice_date', 'invoice_no', 'price',
                'deprecation_rate', 'source', 'request_date', 'provider',
                'provider_order_date', 'delivery_date', 'deprecation_end_date',
                'force_deprecation'
            )
        }),
        (_('User Info'), {
            'fields': (
                'user', 'owner'
            )
        }),
    )


@admin.register(Warehouse)
class WarehousAdmin(reversion.VersionAdmin):
    pass
