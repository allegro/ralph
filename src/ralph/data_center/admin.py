# -*- coding: utf-8 -*-
import operator
from functools import reduce

from django.conf import settings
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.views.main import ChangeList, ORDER_VAR
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ralph.admin.decorators import register
from ralph.admin.filters import (
    BaseObjectHostnameFilter,
    ChoicesListFilter,
    IPFilter,
    LiquidatedStatusFilter,
    MacAddressFilter,
    RelatedAutocompleteFieldListFilter,
    TagsListFilter,
    TreeRelatedAutocompleteFilterWithDescendants,
)
from ralph.admin.helpers import generate_html_link
from ralph.admin.mixins import (
    BulkEditChangeListMixin,
    RalphAdmin,
    RalphAdminImportExportMixin,
    RalphTabularInline,
)
from ralph.admin.views.extra import RalphDetailViewAdmin
from ralph.admin.views.main import RalphChangeList
from ralph.admin.views.multiadd import MulitiAddAdminMixin
from ralph.assets.invoice_report import AssetInvoiceReportMixin
from ralph.assets.models.base import BaseObject, BaseObjectPolymorphicQuerySet
from ralph.assets.models.components import Ethernet
from ralph.assets.views import ComponentsAdminView
from ralph.attachments.admin import AttachmentsMixin
from ralph.data_center.admin_actions import assign_management_hostname_and_ip
from ralph.data_center.forms import DataCenterAssetForm
from ralph.data_center.models.components import DiskShare, DiskShareMount
from ralph.data_center.models.hosts import DCHost
from ralph.data_center.models.physical import (
    Accessory,
    Connection,
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory,
    ServerRoom,
)
from ralph.data_center.models.virtual import (
    BaseObjectCluster,
    Cluster,
    ClusterType,
    Database,
)
from ralph.data_center.views import RelationsView
from ralph.data_importer import resources
from ralph.deployment.mixins import ActiveDeploymentMessageMixin
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.table.table import Table
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.lib.visibility_scope.filters import visibility_scope_filter
from ralph.licences.models import BaseObjectLicence
from ralph.networks.forms import SimpleNetworkWithManagementIPForm
from ralph.networks.views import NetworkWithTerminatorsView
from ralph.operations.views import OperationViewReadOnlyForExisiting
from ralph.supports.models import BaseObjectsSupport


def generate_list_filter_with_common_fields(prefix=None, postfix=None):
    result = []
    if type(prefix) is list:
        result.extend(prefix)
    result.extend(
        [
            "service_env",
            "configuration_path__path",
            (
                "configuration_path__module",
                TreeRelatedAutocompleteFilterWithDescendants,
            ),
            MacAddressFilter,
            IPFilter,
        ]
    )
    if type(postfix) is list:
        result.extend(postfix)
    return result


class DCHostTypeListFilter(ChoicesListFilter):
    def __init__(self, *args, **kwargs):
        from ralph.data_center.models import Cluster, DataCenterAsset
        from ralph.virtual.models import CloudHost, VirtualServer

        models = [Cluster, DataCenterAsset, CloudHost, VirtualServer]
        self.choices_list = [
            (ContentType.objects.get_for_model(model).pk, model._meta.verbose_name)
            for model in models
        ]
        super().__init__(*args, **kwargs)


class DCHostHostnameFilter(SimpleListFilter):
    title = _("Hostname")
    parameter_name = "hostname"
    template = "admin/filters/text_filter.html"

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        fields = [
            "asset__hostname",
            "cloudhost__hostname",
            "cluster__hostname",
            "virtualserver__hostname",
            "ethernet_set__ipaddress__hostname",
        ]
        # TODO: simple if hostname would be in one model
        queries = [
            Q(**{"{}__icontains".format(field): self.value().strip()})
            for field in fields
        ]
        return queryset.filter(reduce(operator.or_, queries)).distinct()

    def lookups(self, request, model_admin):
        return ((1, _("Hostname")),)

    def choices(self, cl):
        yield {
            "selected": self.value(),
            "parameter_name": self.parameter_name,
        }


if settings.ENABLE_DNSAAS_INTEGRATION:
    from ralph.dns.views import DNSView

    class ClusterDNSView(DNSView):
        pass


@register(Accessory)
class AccessoryAdmin(RalphAdmin):
    search_fields = ["name"]


class ClusterNetworkInline(RalphTabularInline):
    form = SimpleNetworkWithManagementIPForm
    model = Ethernet
    exclude = ["model"]


class ClusterLicencesView(RalphDetailViewAdmin):
    icon = "key"
    name = "cluster_licences"
    label = _("Licences")
    url_name = "licences"

    class ClusterLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ("licence",)
        extra = 1

    inlines = [ClusterLicenceInline]


@register(ClusterType)
class ClusterTypeAdmin(RalphAdmin):
    search_fields = ["name"]


@register(Cluster)
class ClusterAdmin(CustomFieldValueAdminMixin, RalphAdmin):
    search_fields = ["name", "hostname", "ethernet_set__ipaddress__hostname"]
    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "name",
                    "hostname",
                    "type",
                    "status",
                    "remarks",
                    "service_env",
                    "configuration_path",
                    "tags",
                )
            },
        ),
    )
    raw_id_fields = ["service_env", "configuration_path"]
    readonly_fields = ["get_masters_summary"]
    list_display = ["id", "name", "hostname", "type"]
    list_select_related = ["type"]
    list_filter = [
        "name",
        BaseObjectHostnameFilter,
        "type",
        "service_env",
        "configuration_path",
        "status",
    ]
    change_views = [ClusterLicencesView]
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views += [ClusterDNSView]

    class ClusterBaseObjectInline(RalphTabularInline):
        model = BaseObjectCluster
        fk_name = "cluster"
        raw_id_fields = ("base_object",)
        extra = 1
        verbose_name = _("Base Object")

    inlines = [ClusterBaseObjectInline, ClusterNetworkInline]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).filter(visibility_scope_filter(request.user))
        )

    def get_fieldsets(self, request, obj=None):
        """
        Attach master info fieldset only if show_master_summary option checked
        for cluster type.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.pk and obj.type.show_master_summary:
            fieldsets += ((_("Master Info"), {"fields": ("get_masters_summary",)}),)
        return fieldsets

    @mark_safe
    def get_masters_summary(self, obj):
        masters = obj.masters
        if not masters:
            return "-"
        return Table(
            masters,
            getattr(masters[0], "_summary_fields", []),
            transpose=True,
        ).render()

    get_masters_summary.short_description = _("Master info")


@register(DataCenter)
class DataCenterAdmin(RalphAdmin):
    list_display = [
        "name",
        "company",
        "country",
        "city",
        "address",
        "latitude",
        "longitude",
        "type",
        "shortcut",
    ]
    search_fields = ["name", "shortcut"]
    list_filter = ["name", "company", "country", "city", "address", "type", "shortcut"]


class DataCenterAssetNetworkView(NetworkWithTerminatorsView):
    pass


class DataCenterAssetSupport(RalphDetailViewAdmin):
    icon = "bookmark"
    name = "dc_asset_support"
    label = _("Supports")
    url_name = "data_center_asset_support"

    class DataCenterAssetSupportInline(RalphTabularInline):
        model = BaseObjectsSupport
        raw_id_fields = ("support",)
        extra = 1
        verbose_name = _("Support")
        ordering = ["-support__date_to"]

    inlines = [DataCenterAssetSupportInline]


class DataCenterAssetLicence(RalphDetailViewAdmin):
    icon = "key"
    name = "dc_asset_licences"
    label = _("Licences")
    url_name = "data_center_asset_licences"

    class DataCenterAssetLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ("licence",)
        extra = 1

    inlines = [DataCenterAssetLicenceInline]


class DataCenterAssetComponents(ComponentsAdminView):
    pass


class DataCenterAssetOperation(OperationViewReadOnlyForExisiting):
    name = "dc_asset_operations"
    url_name = "data_center_asset_operations"
    inlines = OperationViewReadOnlyForExisiting.admin_class.inlines


class DataCenterAssetChangeList(RalphChangeList):
    def get_ordering(self, request, queryset):
        """Adds extra ordering params for ordering by location."""

        # NOTE(romcheg): slot_no is added by Django Admin automatically.
        location_fields = [
            "rack__server_room__data_center__name",
            "rack__server_room__name",
            "rack__name",
            "position",
        ]

        ordering = super(DataCenterAssetChangeList, self).get_ordering(
            request, queryset
        )

        params = self.params
        if ORDER_VAR in params:
            order_params = params[ORDER_VAR].split(".")
            for insert_index, p in enumerate(order_params):
                try:
                    none, pfx, idx = p.rpartition("-")
                    if self.list_display[int(idx)] == "show_location":
                        ordering[insert_index:insert_index] = [
                            "{}{}".format(pfx, field) for field in location_fields
                        ]
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        return ordering


class DataCenterAssetRelationsView(RelationsView):
    url = "datacenterasset_relations"


@register(DataCenterAsset)
class DataCenterAssetAdmin(
    ActiveDeploymentMessageMixin,
    MulitiAddAdminMixin,
    TransitionAdminMixin,
    BulkEditChangeListMixin,
    AttachmentsMixin,
    AssetInvoiceReportMixin,
    CustomFieldValueAdminMixin,
    RalphAdmin,
):
    """Data Center Asset admin class."""

    add_form_template = "data_center/datacenterasset/add_form.html"
    actions = ["bulk_edit_action", "invoice_report", "assign_mgmt_hostname"]

    change_views = [
        DataCenterAssetComponents,
        DataCenterAssetNetworkView,
        DataCenterAssetRelationsView,
        DataCenterAssetLicence,
        DataCenterAssetSupport,
        DataCenterAssetOperation,
    ]
    form = DataCenterAssetForm
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views += [DNSView]
    show_transition_history = True
    resource_class = resources.DataCenterAssetResource
    list_display = [
        "hostname",
        "status",
        "barcode",
        "model",
        "sn",
        "invoice_date",
        "invoice_no",
        "show_location",
        "service_env",
        "configuration_path",
        "property_of",
        "order_no",
    ]
    multiadd_summary_fields = list_display + ["rack"]
    one_of_mulitvalue_required = ["sn", "barcode"]
    bulk_edit_list = [
        "hostname",
        "status",
        "barcode",
        "model",
        "sn",
        "invoice_date",
        "invoice_no",
        "rack",
        "orientation",
        "position",
        "slot_no",
        "price",
        "provider",
        "service_env",
        "configuration_path",
        "tags",
        "production_year",
        "start_usage",
        "depreciation_end_date",
        "depreciation_rate",
        "order_no",
        "remarks",
        "property_of",
    ]
    bulk_edit_no_fillable = ["barcode", "sn"]
    search_fields = [
        "barcode",
        "sn",
        "hostname",
        "invoice_no",
        "order_no",
        "ethernet_set__ipaddress__address",
        "ethernet_set__ipaddress__hostname",
    ]
    list_filter_prefix = ["hostname"]
    list_filter_postfix = [
        "invoice_no",
        "invoice_date",
        "status",
        "barcode",
        "sn",
        "order_no",
        "model__name",
        ("model__category", RelatedAutocompleteFieldListFilter),
        "depreciation_end_date",
        "force_depreciation",
        "remarks",
        "budget_info",
        "rack",
        "rack__server_room",
        "rack__server_room__data_center",
        "position",
        "property_of",
        LiquidatedStatusFilter,
        TagsListFilter,
        "fibrechannelcard_set__wwn",
    ]
    list_filter = generate_list_filter_with_common_fields(
        list_filter_prefix, list_filter_postfix
    )
    date_hierarchy = "created"
    list_select_related = [
        "model",
        "model__manufacturer",
        "model__category",
        "rack",
        "rack__server_room",
        "rack__server_room__data_center",
        "service_env",
        "service_env__service",
        "service_env__environment",
        "configuration_path",
        "property_of",
        "parent",
        "budget_info",
    ]
    raw_id_fields = [
        "model",
        "rack",
        "service_env",
        "parent",
        "budget_info",
        "configuration_path",
    ]
    raw_id_override_parent = {"parent": DataCenterAsset}
    _invoice_report_name = "invoice-data-center-asset"
    readonly_fields = ["get_created_date", "go_to_visualization"]

    fieldsets = (
        (
            _("Basic info"),
            {
                "fields": (
                    "hostname",
                    "model",
                    "status",
                    "barcode",
                    "sn",
                    "niw",
                    "required_support",
                    "remarks",
                    "tags",
                    "property_of",
                    "firmware_version",
                    "bios_version",
                )
            },
        ),
        (
            _("Location Info"),
            {
                "fields": (
                    "rack",
                    "position",
                    "orientation",
                    "slot_no",
                    "parent",
                    "management_ip",
                    "management_hostname",
                    "go_to_visualization",
                )
            },
        ),
        (
            _("Usage info"),
            {
                "fields": (
                    "service_env",
                    "configuration_path",
                    "production_year",
                    "production_use_date",
                )
            },
        ),
        (
            _("Financial & Order Info"),
            {
                "fields": (
                    "order_no",
                    "invoice_date",
                    "invoice_no",
                    "task_url",
                    "price",
                    "vendor_contract_number",
                    "leasing_rate",
                    "depreciation_rate",
                    "depreciation_end_date",
                    "force_depreciation",
                    "source",
                    "provider",
                    "delivery_date",
                    "budget_info",
                    "start_usage",
                    "get_created_date",
                )
            },
        ),
    )

    def assign_mgmt_hostname(self, *args, **kwargs):
        return assign_management_hostname_and_ip(self, *args, **kwargs)

    assign_mgmt_hostname.short_description = "Assign management hostname and IP"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).filter(visibility_scope_filter(request.user))
        )

    def get_export_queryset(self, request):
        qs = (
            super(RalphAdminImportExportMixin, self)
            .get_export_queryset(request)
            .select_related(*self.list_select_related)
        )
        if isinstance(qs, BaseObjectPolymorphicQuerySet):
            return qs.polymorphic_prefetch_related(
                DataCenterAsset=[
                    "tags",
                    "ethernet_set__ipaddress",
                    "parent__ethernet_set__ipaddress",
                ]
            )
        else:
            return qs.prefetch_related(
                "tags", "ethernet_set__ipaddress", "parent__ethernet_set__ipaddress"
            )

    def get_multiadd_fields(self, obj=None):
        multiadd_fields = [
            {"field": "sn", "allow_duplicates": False},
            {"field": "barcode", "allow_duplicates": False},
        ]
        return (
            getattr(settings, "MULTIADD_DATA_CENTER_ASSET_FIELDS", None)
            or multiadd_fields
        )

    @mark_safe
    def go_to_visualization(self, obj):
        if not obj.rack:
            return "&mdash;"
        url = "{}#/sr/{}/rack/{}".format(
            reverse("dc_view"),
            obj.rack.server_room_id,
            obj.rack.id,
        )
        label = "&nbsp;/&nbsp;".join(obj.get_location())
        return generate_html_link(url, label=label, params={})

    go_to_visualization.short_description = _("Visualization")

    @mark_safe
    def show_location(self, obj):
        return obj.location

    show_location.short_description = _("Location")

    # NOTE(romcheg): Django Admin can only order custom fields by one field.
    #                The rest of the ordering is configured in
    #                DataCenterAssetChangeList.get_ordering()
    show_location.admin_order_field = "slot_no"

    def get_created_date(self, obj):
        """
        Return created date for asset (since created is blacklisted by
        permissions, it cannot be displayed directly, because only superuser
        will see it)
        """
        return obj.created or "-"

    get_created_date.short_description = _("Created at")

    def get_changelist(self, request, **kwargs):
        return DataCenterAssetChangeList


@register(ServerRoom)
class ServerRoomAdmin(RalphAdmin):
    list_select_related = ["data_center"]
    search_fields = ["name", "data_center__name"]
    resource_class = resources.ServerRoomResource
    list_display = ["name", "data_center"]


class RackAccessoryInline(RalphTabularInline):
    model = RackAccessory


@register(Rack)
class RackAdmin(RalphAdmin):
    exclude = ["accessories"]
    list_display = [
        "name",
        "server_room_name",
        "data_center_name",
        "reverse_ordering",
    ]
    list_filter = ["server_room__data_center"]  # TODO use fk field in filter
    list_select_related = ["server_room", "server_room__data_center"]
    search_fields = ["name"]
    inlines = [RackAccessoryInline]
    resource_class = resources.RackResource

    def server_room_name(self, obj):
        return obj.server_room.name if obj.server_room else ""

    server_room_name.short_description = _("Server room")
    server_room_name.admin_order_field = "server_room__name"

    def data_center_name(self, obj):
        return obj.server_room.data_center.name if obj.server_room else ""

    data_center_name.short_description = _("Data Center")
    data_center_name.admin_order_field = "server_room__data_center__name"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "server_room":
            kwargs["queryset"] = ServerRoom.objects.select_related(
                "data_center",
            )
        return super(RackAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@register(RackAccessory)
class RackAccessoryAdmin(RalphAdmin):
    list_select_related = ["rack", "accessory"]
    search_fields = ["accessory__name", "rack__name"]
    raw_id_fields = ["rack"]
    list_display = ["__str__", "position"]
    resource_class = resources.RackAccessoryResource


@register(Database)
class DatabaseAdmin(RalphAdmin):
    pass


@register(Connection)
class ConnectionAdmin(RalphAdmin):
    resource_class = resources.ConnectionResource


@register(DiskShare)
class DiskShareAdmin(RalphAdmin):
    pass


@register(DiskShareMount)
class DiskShareMountAdmin(RalphAdmin):
    pass


class DCHostChangeList(ChangeList):
    def url_for_result(self, result):
        return result.get_absolute_url()


@register(DCHost)
class DCHostAdmin(RalphAdmin):
    change_list_template = "admin/data_center/dchost/change_list.html"
    search_fields = [
        "remarks",
        "asset__hostname",
        "cloudhost__hostname",
        "cluster__hostname",
        "virtualserver__hostname",
        "ethernet_set__ipaddress__address",
        "ethernet_set__ipaddress__hostname",
    ]
    list_display = [
        "get_hostname",
        "content_type",
        "service_env",
        "configuration_path",
        "show_location",
        "remarks",
    ]
    # TODO: sn
    # TODO: hostname, DC
    list_filter_prefix = [DCHostHostnameFilter]
    list_filter_postfix = [
        (
            "content_type",
            DCHostTypeListFilter,
        )
    ]
    list_filter = generate_list_filter_with_common_fields(
        list_filter_prefix, list_filter_postfix
    )

    list_select_related = [
        "content_type",
        "configuration_path",
        "service_env",
        "service_env__environment",
        "service_env__service",
    ]

    resource_class = resources.DCHostResource

    def has_add_permission(self, request):
        return False

    def get_changelist(self, request, **kwargs):
        return DCHostChangeList

    def get_actions(self, request):
        return None

    def get_hostname(self, obj):
        return obj.hostname

    get_hostname.short_description = _("Hostname")

    def _initialize_search_form(self, extra_context, fields_from_model=True):
        return super()._initialize_search_form(extra_context)

    @mark_safe
    def show_location(self, obj):
        if hasattr(obj, "get_location"):
            return " / ".join(obj.get_location())
        return ""

    show_location.short_description = _("Location")

    def get_queryset(self, request):
        qs = super().get_queryset(request).filter(visibility_scope_filter(request.user))
        # location
        polymorphic_select_related = dict(
            DataCenterAsset=["rack__server_room__data_center", "model"],
            VirtualServer=[
                "parent__asset__datacenterasset__rack__server_room__data_center",  # noqa
            ],
            CloudHost=["hypervisor__rack__server_room__data_center"],
        )
        qs = qs.polymorphic_select_related(**polymorphic_select_related)
        qs = qs.polymorphic_prefetch_related(
            Cluster=[
                Prefetch(
                    "baseobjectcluster_set__base_object",
                    queryset=BaseObject.polymorphic_objects.polymorphic_select_related(  # noqa
                        **polymorphic_select_related
                    ),
                )
            ]
        )
        return qs
