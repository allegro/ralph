# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.filters import (
    BarcodeFilter,
    DepreciationDateFilter,
    ForceDepreciationFilter,
    HostnameFilter,
    InvoiceDateFilter,
    InvoiceNoFilter,
    ModelFilter,
    OrderNoFilter,
    RemarksFilter,
    SNFilter,
    StatusFilter
)
from ralph.back_office.models import BackOfficeAsset, Warehouse
from ralph.back_office.views import (
    BackOfficeAssetComponents,
    BackOfficeAssetSoftware
)
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence


class BackOfficeAssetSupport(RalphDetailViewAdmin):
    icon = 'bookmark'
    name = 'bo_asset_support'
    label = _('Supports')
    url_name = 'back_office_asset_support'

    class BackOfficeAssetSupportInline(RalphTabularInline):
        model = BackOfficeAsset.supports.related.through
        raw_id_fields = ('support',)
        extra = 1
        verbose_name = _('Support')

    inlines = [BackOfficeAssetSupportInline]


class BackOfficeAssetLicence(RalphDetailViewAdmin):

    icon = 'key'
    name = 'bo_asset_licence'
    label = _('Licence')
    url_name = 'back_office_asset_licence'

    class BackOfficeAssetLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ('licence',)
        extra = 1
        verbose_name = _('Licence')

    inlines = [BackOfficeAssetLicenceInline]


@register(BackOfficeAsset)
class BackOfficeAssetAdmin(
    MulitiAddAdminMixin,
    BulkEditChangeListMixin,
    PermissionAdminMixin,
    TransitionAdminMixin,
    RalphAdmin
):

    """Back Office Asset admin class."""
    actions = ['bulk_edit_action']
    change_views = [
        BackOfficeAssetComponents,
        BackOfficeAssetSoftware,
        BackOfficeAssetLicence,
        BackOfficeAssetSupport,
    ]
    list_display = [
        'status', 'barcode', 'purchase_order', 'model', 'user', 'warehouse',
        'sn', 'hostname', 'invoice_date', 'invoice_no', 'region',
    ]
    multiadd_info_fields = list_display

    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']
    list_filter = [
        StatusFilter, BarcodeFilter, SNFilter, HostnameFilter, InvoiceNoFilter,
        InvoiceDateFilter, OrderNoFilter, ModelFilter, DepreciationDateFilter,
        ForceDepreciationFilter, RemarksFilter
    ]
    date_hierarchy = 'created'
    list_select_related = [
        'model', 'user', 'warehouse', 'model__manufacturer', 'region'
    ]
    raw_id_fields = ['model', 'user', 'owner', 'service_env']
    resource_class = resources.BackOfficeAssetResource
    bulk_edit_list = list_display

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'hostname', 'model', 'barcode', 'sn', 'niw', 'status',
                'warehouse', 'location', 'region', 'loan_end_date',
                'service_env', 'remarks'
            )
        }),
        (_('User Info'), {
            'fields': (
                'user', 'owner'
            )
        }),
        (_('Financial Info'), {
            'fields': (
                'order_no', 'purchase_order', 'invoice_date', 'invoice_no',
                'task_url', 'price', 'depreciation_rate',
                'depreciation_end_date', 'force_depreciation', 'provider',

            )
        }),
    )

    def get_multiadd_fields(self):
        return ['sn', 'barcode']


@register(Warehouse)
class WarehouseAdmin(RalphAdmin):

    search_fields = ['name']
