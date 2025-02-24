# -*- coding: utf-8 -*-
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import TagsListFilter
from ralph.admin.helpers import generate_html_link
from ralph.admin.mixins import (
    BulkEditChangeListMixin,
    RalphAdmin,
    RalphTabularInline
)
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_importer import resources
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.mixins.forms import PriceFormMixin
from ralph.supports.models import BaseObjectsSupport, Support, SupportType


class BaseObjectSupportView(RalphDetailViewAdmin):
    icon = "laptop"
    name = "base-object-assignments"
    label = _("Assignments")
    url_name = "assignments"

    class BaseObjectSupportInline(RalphTabularInline):
        model = BaseObjectsSupport
        raw_id_fields = ("baseobject",)
        extra = 1
        verbose_name = _("assignments")
        verbose_name_plural = _("Assignments")
        fk_name = "support"

    inlines = [BaseObjectSupportInline]


class SupportAdminForm(PriceFormMixin, RalphAdmin.form):
    """
    Service_env is not required for Supports.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # backward compatibility
        service_env_field = self.fields.get("service_env", None)
        if service_env_field:
            service_env_field.required = False


@register(Support)
class SupportAdmin(
    AttachmentsMixin, CustomFieldValueAdminMixin, BulkEditChangeListMixin, RalphAdmin
):
    """Support model admin class."""

    change_views = [BaseObjectSupportView]
    actions = ["bulk_edit_action"]
    form = SupportAdminForm
    search_fields = ["name", "serial_no", "contract_id", "description", "remarks"]
    list_filter = [
        "contract_id",
        "name",
        "serial_no",
        "price",
        "remarks",
        "description",
        "support_type",
        "budget_info",
        "date_from",
        "date_to",
        "property_of",
        TagsListFilter,
    ]
    date_hierarchy = "created"
    list_display = [
        "support_type",
        "contract_id",
        "name",
        "serial_no",
        "service_env",
        "date_from",
        "date_to",
        "created",
        "remarks",
        "description",
    ]
    bulk_edit_list = [
        "status",
        "asset_type",
        "contract_id",
        "description",
        "price",
        "date_from",
        "date_to",
        "escalation_path",
        "contract_terms",
        "sla_type",
        "producer",
        "supplier",
        "serial_no",
        "service_env",
        "invoice_no",
        "invoice_date",
        "period_in_months",
        "property_of",
        "budget_info",
        "support_type",
    ]
    list_select_related = [
        "support_type",
        "service_env",
        "service_env__service",
        "service_env__environment",
    ]
    resource_class = resources.SupportResource
    raw_id_fields = ["budget_info", "region", "support_type", "service_env"]
    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "support_type",
                    "name",
                    "status",
                    "producer",
                    "description",
                    "date_from",
                    "date_to",
                    "serial_no",
                    "escalation_path",
                    "region",
                    "remarks",
                    "service_env",
                )
            },
        ),
        (
            _("Contract info"),
            {
                "fields": (
                    "contract_id",
                    "contract_terms",
                    "sla_type",
                    "price",
                    "supplier",
                    "invoice_date",
                    "invoice_no",
                    "budget_info",
                    "period_in_months",
                    "property_of",
                )
            },
        ),
    )

    _export_queryset_manager = "objects_with_related"


@register(SupportType)
class SupportTypeAdmin(RalphAdmin):
    resource_class = resources.SupportTypeResource
    search_fields = ["name"]


@register(BaseObjectsSupport)
class BaseObjectsSupportAdmin(RalphAdmin):
    redirect_to_detail_view_if_one_search_result = False
    resource_class = resources.BaseObjectsSupportRichResource
    search_fields = [
        "support__name",
        "support__serial_no",
        "support__contract_id",
        "support__description",
        "support__remarks",
    ]
    list_filter = [
        "support__contract_id",
        "support__name",
        "support__serial_no",
        "support__price",
        "support__support_type",
        "support__budget_info",
        "support__date_from",
        "support__date_to",
        "support__property_of",
        "baseobject__asset__barcode",
        "baseobject__asset__sn",
        "baseobject__asset__hostname",
        "baseobject__asset__service_env",
    ]
    list_display = [
        "_get_support_type",
        "_get_support_contract_id",
        "_get_support_name",
        "_get_support_price",
        "_get_support_date_from",
        "_get_support_date_to",
        "_get_asset_hostname",
        "_get_asset_service_env",
    ]
    raw_id_fields = ["support", "baseobject"]
    list_select_related = [
        "support",
        "support__support_type",
        "baseobject__asset",
        "baseobject__service_env__service",
        "baseobject__service_env__environment",
    ]

    list_display_links = None
    actions = None

    def get_queryset(self, request):
        # fetch additional objects_count for exporter
        return (
            super()
            .get_queryset(request)
            .annotate(objects_count=Count("support__baseobjectssupport"))
        )

    # disable edit view, adding and deleting objects from here
    def change_view(self, request, obj=None):
        opts = self.model._meta
        url = reverse(
            "admin:{app}_{model}_changelist".format(
                app=opts.app_label,
                model=opts.model_name,
            )
        )
        return HttpResponseRedirect(url)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # list display fields (django admin does not support __ convention there,
    # so they have to be fetched "manually")
    @mark_safe
    def _get_support_type(self, obj):
        return generate_html_link(
            obj.support.get_absolute_url(),
            label=obj.support.support_type,
            params={},
        )

    _get_support_type.short_description = _("support type")
    _get_support_type.admin_order_field = "support__support_type"

    def _get_support_contract_id(self, obj):
        return obj.support.contract_id

    _get_support_contract_id.short_description = _("support contract id")
    _get_support_contract_id.admin_order_field = "support__contract_id"

    def _get_support_name(self, obj):
        return obj.support.contract_id

    _get_support_name.short_description = _("support name")
    _get_support_name.admin_order_field = "support__name"

    def _get_support_price(self, obj):
        return obj.support.price

    _get_support_price.short_description = _("support price")
    _get_support_price.admin_order_field = "support__price"

    def _get_support_date_from(self, obj):
        return obj.support.date_from

    _get_support_date_from.short_description = _("support date from")
    _get_support_date_from.admin_order_field = "support__date_from"

    def _get_support_date_to(self, obj):
        return obj.support.date_to

    _get_support_date_to.short_description = _("support date to")
    _get_support_date_to.admin_order_field = "support__date_to"

    @mark_safe
    def _get_asset_hostname(self, obj):
        return generate_html_link(
            obj.baseobject.get_absolute_url(),
            label=obj.baseobject.asset.hostname,
            params={},
        )

    _get_asset_hostname.short_description = _("asset hostname")
    _get_asset_hostname.admin_order_field = "baseobject__asset__hostname"

    def _get_asset_service_env(self, obj):
        return obj.baseobject.service_env

    _get_asset_service_env.short_description = _("asset service env")
    _get_asset_service_env.admin_order_field = "baseobject__service_env__service__name"  # noqa
