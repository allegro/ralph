# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, register
from ralph.back_office.models import BackOfficeAsset, Warehouse
from ralph.back_office.views import (
    BackOfficeAssetComponents,
    BackOfficeAssetSoftware,
)


@register(BackOfficeAsset)
class BackOfficeAssetAdmin(RalphAdmin):

    """Back Office Asset admin class."""

    change_views = [
        BackOfficeAssetComponents,
        BackOfficeAssetSoftware,
    ]
    list_display = [
        'status', 'barcode', 'purchase_order', 'model', 'user', 'warehouse',
        'sn', 'hostname', 'invoice_date', 'invoice_no'
    ]
    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = ['status']
    date_hierarchy = 'created'
    list_select_related = ['model', 'user', 'warehouse', 'model__manufacturer']
    raw_id_fields = ['model', 'user', 'owner', 'service_env']

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


@register(Warehouse)
class WarehouseAdmin(RalphAdmin):
    pass
