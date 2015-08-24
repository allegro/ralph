# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.admin.filters import (
    BooleanFilter,
    ChoicesFilter,
    DateFilter,
    TextFilter
)
from ralph.assets.models.choices import AssetStatus


class BarcodeFilter(TextFilter):

    title = _('Barcode')
    parameter_name = 'barcode'


class SNFilter(TextFilter):

    title = _('SN')
    parameter_name = 'sn'


class StatusFilter(ChoicesFilter):

    title = _('Status')
    parameter_name = 'status'
    choices_list = AssetStatus()


class ModelFilter(TextFilter):

    title = _('Model')
    parameter_name = 'model__name'


class HostnameFilter(TextFilter):

    title = _('Hostname')
    parameter_name = 'hostname'


class RemarksFilter(TextFilter):

    title = _('Remarks')
    parameter_name = 'remarks'


class DepreciationDateFilter(DateFilter):

    title = _('Depreciation date')
    parameter_name = 'depreciation_end_date'
    parameter_name_start = 'depreciation_end_date_start'
    parameter_name_end = 'depreciation_end_date_end'


class ForceDepreciationFilter(BooleanFilter):

    title = _('Force depreciation')
    parameter_name = 'force_depreciation'


class InvoiceDateFilter(DateFilter):

    title = _('Invoice date')
    parameter_name = 'invoice_date'
    parameter_name_start = 'invoice_date_start'
    parameter_name_end = 'invoice_date_end'


class InvoiceNoFilter(TextFilter):

    title = _('Invoice no')
    parameter_name = 'invoice_no'


class OrderNoFilter(TextFilter):

    title = _('Order no')
    parameter_name = 'order_no'
