# -*- coding: utf-8 -*-
from django import forms
from django.apps import apps
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import LiquidatedStatusFilter, TagsListFilter
from ralph.admin.mixins import (
    BulkEditChangeListMixin,
    RalphAdmin,
    RalphTabularInline
)
from ralph.admin.sites import ralph_site
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.admin.widgets import AutocompleteWidget
from ralph.assets.filters import BuyoutDateFilter
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models import ObjectModelType
from ralph.attachments.admin import AttachmentsMixin
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)
from ralph.data_importer import resources
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.mixins.forms import AssetFormMixin, PriceFormMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence, Licence
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.supports.models import BaseObjectsSupport


class BackOfficeAssetSupport(RalphDetailViewAdmin):
    icon = "bookmark"
    name = "bo_asset_support"
    label = _("Supports")
    url_name = "back_office_asset_support"

    class BackOfficeAssetSupportInline(RalphTabularInline):
        model = BaseObjectsSupport
        raw_id_fields = ("support",)
        extra = 1
        verbose_name = _("Support")
        ordering = ["-support__date_to"]

    inlines = [BackOfficeAssetSupportInline]


class BackOfficeAssetLicence(RalphDetailViewAdmin):
    icon = "key"
    name = "bo_asset_licence"
    label = _("Licence")
    url_name = "back_office_asset_licence"

    class BackOfficeAssetLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ("licence",)
        extra = 1
        verbose_name = _("Licence")

    inlines = [BackOfficeAssetLicenceInline]


class BackOfficeAssetOperation(OperationViewReadOnlyForExisiting):
    name = "bc_asset_operations"
    url_name = "back_office_asset_operations"
    inlines = OperationViewReadOnlyForExisiting.admin_class.inlines


class BackOfficeAssetAdminForm(PriceFormMixin, AssetFormMixin, RalphAdmin.form):
    MODEL_TYPE = ObjectModelType.back_office
    """
    Service_env is not required for BackOffice assets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "hostname" in self.fields and settings.BACKOFFICE_HOSTNAME_FIELD_READONLY:
            self.fields["hostname"].widget.attrs["readonly"] = True

        # backward compatibility
        service_env_field = self.fields.get("service_env", None)
        if service_env_field:
            service_env_field.required = False


@register(BackOfficeAsset)
class BackOfficeAssetAdmin(
    MulitiAddAdminMixin,
    AttachmentsMixin,
    BulkEditChangeListMixin,
    TransitionAdminMixin,
    AssetInvoiceReportMixin,
    CustomFieldValueAdminMixin,
    RalphAdmin,
):
    """Back Office Asset admin class."""

    add_form_template = "backofficeasset/add_form.html"
    form = BackOfficeAssetAdminForm
    actions = ["bulk_edit_action", "invoice_report"]

    show_transition_history = True
    change_views = [
        BackOfficeAssetLicence,
        BackOfficeAssetSupport,
        BackOfficeAssetOperation,
        # TODO: uncomment the two tabs below once they are ready for use
        # BackOfficeAssetComponents,
        # BackOfficeAssetSoftware,
    ]
    list_display = [
        "status",
        "barcode",
        "purchase_order",
        "model",
        "get_user",
        "warehouse",
        "service_env",
        "sn",
        "hostname",
        "invoice_date",
        "invoice_no",
        "region",
        "property_of",
        "buyout_date_display",
    ]
    multiadd_summary_fields = list_display

    search_fields = ["barcode", "sn", "hostname", "invoice_no", "order_no"]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )  # noqa
        if "barcode" in request.GET:
            barcode = request.GET.get("barcode").split(";")
            queryset = self.model.objects.filter(barcode__in=barcode)
        return queryset, use_distinct

    list_filter = [
        "barcode",
        "status",
        "imei",
        "imei2",
        "sn",
        "model",
        "purchase_order",
        "hostname",
        "required_support",
        "region",
        "warehouse",
        "task_url",
        "model__category",
        "loan_end_date",
        "niw",
        "model__manufacturer",
        "model__manufacturer__manufacturer_kind",
        "location",
        "remarks",
        "user",
        "owner",
        "user__segment",
        "user__company",
        "user__department",
        "user__employee_id",
        "property_of",
        "invoice_no",
        "invoice_date",
        "order_no",
        "provider",
        "budget_info",
        "depreciation_rate",
        "depreciation_end_date",
        "force_depreciation",
        ("buyout_date", BuyoutDateFilter),
        LiquidatedStatusFilter,
        TagsListFilter,
        "service_env",
    ]
    date_hierarchy = "created"
    list_select_related = [
        "model",
        "user",
        "warehouse",
        "model__manufacturer",
        "region",
        "model__category",
        "property_of",
        "service_env",
        "service_env__service",
        "service_env__environment",
    ]
    raw_id_fields = [
        "model",
        "user",
        "owner",
        "region",
        "warehouse",
        "property_of",
        "budget_info",
        "office_infrastructure",
        "service_env",
    ]
    resource_class = resources.BackOfficeAssetResource
    bulk_edit_list = [
        "licences",
        "status",
        "barcode",
        "imei",
        "imei2",
        "hostname",
        "model",
        "purchase_order",
        "user",
        "owner",
        "warehouse",
        "sn",
        "region",
        "property_of",
        "remarks",
        "invoice_date",
        "invoice_no",
        "provider",
        "task_url",
        "service_env",
        "depreciation_rate",
        "price",
        "order_no",
        "depreciation_end_date",
        "tags",
        "start_usage",
    ]
    bulk_edit_no_fillable = ["barcode", "sn", "imei", "imei2", "hostname"]
    _invoice_report_name = "invoice-back-office-asset"
    _invoice_report_item_fields = (
        AssetInvoiceReportMixin._invoice_report_item_fields + ["owner"]
    )
    _invoice_report_select_related = (
        AssetInvoiceReportMixin._invoice_report_select_related + ["owner"]
    )

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "hostname",
                    "model",
                    "barcode",
                    "sn",
                    "imei",
                    "imei2",
                    "niw",
                    "status",
                    "last_status_change",
                    "warehouse",
                    "location",
                    "region",
                    "loan_end_date",
                    "remarks",
                    "tags",
                    "property_of",
                    "task_url",
                    "service_env",
                    "office_infrastructure",
                )
            },
        ),
        (_("User Info"), {"fields": ("user", "owner")}),
        (
            _("Financial Info"),
            {
                "fields": (
                    "order_no",
                    "purchase_order",
                    "invoice_date",
                    "invoice_no",
                    "price",
                    "depreciation_rate",
                    "depreciation_end_date",
                    "force_depreciation",
                    "provider",
                    "budget_info",
                    "start_usage",
                )
            },
        ),
    )

    def licences(self, obj):
        return ""

    licences.short_description = "licences"

    def buyout_date_display(self, obj):
        if obj.model.category.show_buyout_date:
            return obj.buyout_date
        return None

    buyout_date_display.short_description = _("buyout date")
    buyout_date_display.admin_order_field = "buyout_date"

    def get_changelist_form(self, request, **kwargs):
        """
        Returns a Form class for use in the Formset on the changelist page.
        """
        Form = super().get_changelist_form(request, **kwargs)

        class BackOfficeAssetBulkForm(Form):
            """
            Adds Licence field in bulk form.

            Because of models (licence is many-to-many with base-object)
            editing licence on asset form is impossible with regular
            Django-Admin features. This solves that.
            """

            licences = forms.ModelMultipleChoiceField(
                queryset=Licence.objects.all(),
                label=_("licences"),
                required=False,
                widget=AutocompleteWidget(
                    field=apps.get_model("licences.BaseObjectLicence")._meta.get_field(
                        "licence"
                    ),
                    admin_site=ralph_site,
                    request=request,
                    multi=True,
                ),
            )

            def __init__(self, *args, **kwargs):
                initial = kwargs.get("initial", {})
                initial["licences"] = [
                    # TODO: permissions handling: now this field is only visible
                    # to superusers
                    str(_id)
                    for _id in kwargs["instance"].licences.values_list(
                        "licence__id", flat=True
                    )
                ]
                kwargs["initial"] = initial
                super().__init__(*args, **kwargs)

            def save_m2m(self):
                form_licences = self.cleaned_data["licences"]

                form_licences_ids = [licence.id for licence in form_licences]
                asset_licences_ids = self.instance.licences.values_list(
                    "licence__id", flat=True
                )

                to_add = set(form_licences_ids) - set(asset_licences_ids)
                to_remove = set(asset_licences_ids) - set(form_licences_ids)
                for licence in form_licences:
                    if licence.id not in to_add:
                        continue
                    BaseObjectLicence.objects.get_or_create(
                        base_object=self.instance,
                        licence_id=licence.id,
                    )
                self.instance.licences.filter(licence_id__in=to_remove).delete()
                return self.instance

            def save(self, commit=True):
                # commit=True else save_m2m (from this form) won't be called
                instance = super().save(commit=True)
                return instance

        return BackOfficeAssetBulkForm

    def get_multiadd_fields(self, obj=None):
        multi_add_fields = [
            {"field": "sn", "allow_duplicates": False},
            {"field": "barcode", "allow_duplicates": False},
        ]
        # Check only obj, because model is required field
        if obj and obj.model.category.imei_required:
            multi_add_fields.append({"field": "imei", "allow_duplicates": False})
            multi_add_fields.append({"field": "imei2", "allow_duplicates": False})
        return multi_add_fields

    @mark_safe
    def get_user(self, obj):
        if not obj.user_id:
            return "-"
        return '<a href="{}">{} {} ({})<a/>'.format(
            obj.user.get_absolute_url(),
            obj.user.first_name,
            obj.user.last_name,
            obj.user.username,
        )

    get_user.short_description = _("User")
    get_user.admin_order_field = "get_user"


@register(Warehouse)
class WarehouseAdmin(RalphAdmin):
    search_fields = ["name"]


@register(OfficeInfrastructure)
class OfficeInfrastructureAdmin(RalphAdmin):
    search_fields = ["name"]
