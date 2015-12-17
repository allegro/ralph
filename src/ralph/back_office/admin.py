# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.admin.mixins import BulkEditChangeListMixin
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.attachments.admin import AttachmentsMixin
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)
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


from ralph.admin.widgets import AutocompleteManyToManyWidget
from ralph.admin.sites import ralph_site
from ralph.supports.models import BaseObjectsSupport, Support


class AutoCompleteManyToManyField(forms.Field):

    def __init__(self, *args, **kwargs):
        self.to_model = kwargs.pop('to_model')
        self.m2m_model = kwargs.pop('m2m_model')
        self.fk_field_from = kwargs.pop('fk_field_from')
        self.fk_field_to = kwargs.pop('fk_field_to')
        super().__init__(*args, **kwargs)
        self.widget = AutocompleteManyToManyWidget(
            field=self, admin_site=ralph_site,
            rel_to=Support, many_to_many=True
        )

    def prepare_value(self, value):
        if self.instance:
            qs = self.m2m_model.objects.filter(
                **{self.fk_field_from: self.instance}
            )
            return ','.join(
                map(str, qs.values_list(self.fk_field_to, flat=True))
            )

        return value


class ManyToManyFormMixin(object):

    m2m_fields = {
        'supports': {
            'to_model': Support,
            'm2m_model': BaseObjectsSupport,
            'fk_field_from': 'baseobject',
            'fk_field_to': 'support'
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field, options in self.m2m_fields.items():
        #     self.fields[field] = AutoCompleteManyToManyField(**options)
        #     self.fields[field].widget.request = self._request
        #     self.fields[field].instance = self.instance

    def save(self, commit=True):
        instance = super().save(commit)
        if instance:
            for field, options in self.m2m_fields.items():
                value = self.cleaned_data[field]
                field = self.fields[field]
                old_values = field.m2m_model.objects.filter(
                    **{field.fk_field_from: instance.pk}
                ).values_list(field.fk_field_to, flat=True)
                new_values = []
                for val in value.split(','):
                    if not val:
                        continue
                    new_values.append(int(val))
                    obj, _ = field.m2m_model.objects.get_or_create(
                        **{
                            '{}_id'.format(field.fk_field_to): val,
                            '{}_id'.format(field.fk_field_from): instance.pk
                        }
                    )
                to_delete = list(set(old_values) - set(new_values))
                if to_delete:
                    field.m2m_model.objects.filter(
                        **{
                            field.fk_field_from: instance,
                            '{}__in'.format(field.fk_field_to): to_delete
                        }
                    ).delete()
        return instance


class BackOfficeAssetAdminForm(ManyToManyFormMixin, RalphAdmin.form):
    """
    Service_env is not required for BackOffice assets.
    """
    supports = AutoCompleteManyToManyField(**{
        'to_model': Support,
        'm2m_model': BaseObjectsSupport,
        'fk_field_from': 'baseobject',
        'fk_field_to': 'support',
        'required': False
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'hostname' in self.fields:
            self.fields['hostname'].widget.attrs['readonly'] = True

        for field, options in self.m2m_fields.items():
            self.fields[field].widget.request = self._request
            self.fields[field].instance = self.instance


@register(BackOfficeAsset)
class BackOfficeAssetAdmin(
    MulitiAddAdminMixin,
    AttachmentsMixin,
    BulkEditChangeListMixin,
    PermissionAdminMixin,
    TransitionAdminMixin,
    AssetInvoiceReportMixin,
    RalphAdmin
):

    """Back Office Asset admin class."""
    form = BackOfficeAssetAdminForm
    actions = ['bulk_edit_action']
    show_transition_history = True
    change_views = [
        BackOfficeAssetLicence,
        BackOfficeAssetSupport,
        BackOfficeAssetComponents,
        BackOfficeAssetSoftware,
    ]
    list_display = [
        'status', 'barcode', 'purchase_order', 'model', 'user', 'warehouse',
        'sn', 'hostname', 'invoice_date', 'invoice_no', 'region',
    ]
    multiadd_info_fields = list_display

    search_fields = ['barcode', 'sn', 'hostname', 'invoice_no', 'order_no']

    list_filter = [
        'barcode', 'status', 'imei', 'sn', 'model', 'purchase_order',
        'hostname', 'required_support', 'region',
        'warehouse', 'task_url', 'model__category', 'loan_end_date', 'niw',
        'model__manufacturer', 'location', 'remarks',
        'user', 'owner', 'user__segment', 'user__company', 'user__department',
        'user__employee_id', 'property_of', 'invoice_no', 'invoice_date',
        'order_no', 'provider', 'budget_info',
        'depreciation_rate', 'depreciation_end_date', 'force_depreciation'
    ]
    date_hierarchy = 'created'
    list_select_related = [
        'model', 'user', 'warehouse', 'model__manufacturer', 'region',
        'model__category'
    ]
    raw_id_fields = [
        'model', 'user', 'owner', 'region', 'warehouse',
        'property_of', 'budget_info', 'office_infrastructure'
    ]
    resource_class = resources.BackOfficeAssetResource
    bulk_edit_list = [
        'supports',
        'status', 'barcode', 'imei', 'hostname', 'model', 'purchase_order',
        'user', 'owner', 'warehouse', 'sn', 'region', 'property_of', 'remarks',
        'invoice_date', 'invoice_no', 'provider', 'task_url',
        'depreciation_rate', 'price', 'order_no', 'depreciation_end_date'
    ]
    bulk_edit_no_fillable = ['barcode', 'sn', 'imei', 'hostname']
    _invoice_report_name = 'invoice-back-office-asset'
    _invoice_report_item_fields = (
        AssetInvoiceReportMixin._invoice_report_item_fields + ['owner']
    )
    _invoice_report_select_related = (
        AssetInvoiceReportMixin._invoice_report_select_related + ['owner']
    )

    fieldsets = (
        (_('Basic info'), {
            'fields': (
                'supports',
                'hostname', 'model', 'barcode', 'sn', 'imei', 'niw', 'status',
                'warehouse', 'location', 'region', 'loan_end_date', 'remarks',
                'tags', 'property_of', 'task_url', 'office_infrastructure'
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
                'price', 'depreciation_rate', 'depreciation_end_date',
                'force_depreciation', 'provider', 'budget_info',
            )
        }),
    )

    def get_multiadd_fields(self, obj=None):
        multi_add_fields = [
            {'field': 'sn', 'allow_duplicates': False},
            {'field': 'barcode', 'allow_duplicates': False},
        ]
        # Check only obj, because model is required field
        if obj and obj.model.category.imei_required:
            multi_add_fields.append(
                {'field': 'imei', 'allow_duplicates': False}
            )
        return multi_add_fields


@register(Warehouse)
class WarehouseAdmin(RalphAdmin):

    search_fields = ['name']


@register(OfficeInfrastructure)
class OfficeInfrastructureAdmin(RalphAdmin):
    search_fields = ['name']
