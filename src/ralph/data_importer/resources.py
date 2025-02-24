from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from import_export import fields, resources, widgets

from ralph.accounts.models import Region
from ralph.assets.models import assets, base, BaseObject, configuration
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)
from ralph.data_center.models import hosts, physical
from ralph.data_importer.fields import PriceField, ThroughField
from ralph.data_importer.mixins import (
    ImportForeignKeyMeta,
    ImportForeignKeyMixin
)
from ralph.data_importer.widgets import (
    AssetServiceEnvWidget,
    AssetServiceUidWidget,
    BaseObjectManyToManyWidget,
    BaseObjectServiceNamesM2MWidget,
    BaseObjectWidget,
    ImportedForeignKeyWidget,
    IPManagementWidget,
    ManyToManyThroughWidget,
    PriceAmountWidget,
    PriceCurrencyWidget,
    UserManyToManyWidget,
    UserWidget
)
from ralph.domains.models.domains import Domain, DomainContract
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)
from ralph.networks.models import networks
from ralph.operations.models import Operation, OperationType
from ralph.supports.models import BaseObjectsSupport, Support, SupportType

RalphResourceMeta = type(
    "RalphResourceMeta",
    (ImportForeignKeyMeta, resources.ModelDeclarativeMetaclass, resources.Resource),
    {},
)


class RalphModelResource(
    ImportForeignKeyMixin, resources.ModelResource, metaclass=RalphResourceMeta
):
    pass


class ResourceWithPrice(resources.ModelResource):
    price = PriceField(attribute="price", widget=PriceAmountWidget())
    price_currency = fields.Field(
        attribute="price", readonly=True, widget=PriceCurrencyWidget()
    )


class AssetModelResource(RalphModelResource):
    manufacturer = fields.Field(
        column_name="manufacturer",
        attribute="manufacturer",
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ImportedForeignKeyWidget(assets.Category),
    )
    assets_count = fields.Field(
        readonly=True,
        column_name="assets_count",
        attribute="assets_count",
    )

    class Meta:
        model = assets.AssetModel

    def get_queryset(self):
        return assets.AssetModel.objects.annotate(assets_count=Count("assets"))

    def dehydrate_assets_count(self, model):
        # check if model has `assets_count` attribute first (it's only included
        # when using annotated queryset above)
        return (
            model.assets_count
            if hasattr(model, "assets_count")
            else model.assets.count()
        )


class CategoryResource(RalphModelResource):
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ImportedForeignKeyWidget(assets.Category),
    )

    class Meta:
        model = assets.Category


class BackOfficeAssetResource(ResourceWithPrice, RalphModelResource):
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ImportedForeignKeyWidget(assets.Asset),
    )
    service_env = fields.Field(
        column_name="service_env",
        attribute="service_env",
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, "name"),
    )
    model = fields.Field(
        column_name="model",
        attribute="model",
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    user = fields.Field(
        column_name="user",
        attribute="user",
        widget=UserWidget(get_user_model()),
    )
    owner = fields.Field(
        column_name="owner",
        attribute="owner",
        widget=UserWidget(get_user_model()),
    )
    warehouse = fields.Field(
        column_name="warehouse",
        attribute="warehouse",
        widget=ImportedForeignKeyWidget(Warehouse),
    )
    region = fields.Field(
        column_name="region",
        attribute="region",
        widget=ImportedForeignKeyWidget(Region),
    )
    property_of = fields.Field(
        column_name="property_of",
        attribute="property_of",
        widget=ImportedForeignKeyWidget(assets.AssetHolder),
    )
    budget_info = fields.Field(
        column_name="budget_info",
        attribute="budget_info",
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )

    class Meta:
        model = BackOfficeAsset
        prefetch_related = ("tags",)
        exclude = (
            "content_type",
            "asset_ptr",
            "baseobject_ptr",
        )

    def dehydrate_depreciation_rate(self, bo_asset):
        return str(bo_asset.depreciation_rate)


class ServerRoomResource(RalphModelResource):
    data_center = fields.Field(
        column_name="data_center",
        attribute="data_center",
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )

    class Meta:
        model = physical.ServerRoom


class RackResource(RalphModelResource):
    server_room = fields.Field(
        column_name="server_room",
        attribute="server_room",
        widget=ImportedForeignKeyWidget(physical.ServerRoom),
    )

    class Meta:
        model = physical.Rack


class DiscoveryDataCenterResource(RalphModelResource):
    """
    Imports datacenters from Discovery.DataCenter (Ralph2).

    In Ralph2 data centers was in two tables:
        - Assets data centers
        - Discovery data centers
    Ralph3 stores all data centers in one table (physical.DataCenter), so this
    resource allows to import discovery data centers from Ralph2.
    """

    class Meta:
        model = physical.DataCenter


class NetworkResource(RalphModelResource):
    data_center = fields.Field(
        column_name="data_center",
        attribute="data_center",
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )
    network_environment = fields.Field(
        column_name="network_environment",
        attribute="network_environment",
        widget=ImportedForeignKeyWidget(networks.NetworkEnvironment),
    )
    kind = fields.Field(
        column_name="kind",
        attribute="kind",
        widget=ImportedForeignKeyWidget(networks.NetworkKind),
    )
    terminators = fields.Field(
        column_name="terminators",
        attribute="terminators",
        widget=BaseObjectManyToManyWidget(model=assets.BaseObject),
    )

    class Meta:
        model = networks.Network
        exclude = ("gateway_as_int", "min_ip", "max_ip")


class IPAddressResource(RalphModelResource):
    base_object = fields.Field(
        column_name="asset",
        attribute="base_object",
        widget=BaseObjectWidget(assets.BaseObject),
    )

    network = fields.Field(
        column_name="network",
        attribute="network",
        widget=ImportedForeignKeyWidget(networks.Network),
    )

    class Meta:
        model = networks.IPAddress

    def skip_row(self, instance, original):
        if settings.MAP_IMPORTED_ID_TO_NEW_ID:
            try:
                networks.IPAddress.objects.get(address=instance.address)
            except networks.IPAddress.DoesNotExist:
                pass
            else:
                return True
        return False


class DataCenterAssetResource(ResourceWithPrice, RalphModelResource):
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    parent._exclude_in_select_related = True
    parent_management_ip = fields.Field(
        readonly=True,
        column_name="parent_management_ip",
        attribute="parent_management_ip",
    )
    service_env = fields.Field(
        column_name="service_env",
        attribute="service_env",
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, "name"),
    )
    model = fields.Field(
        column_name="model",
        attribute="model",
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    rack = fields.Field(
        column_name="rack",
        attribute="rack",
        widget=ImportedForeignKeyWidget(physical.Rack),
    )
    budget_info = fields.Field(
        column_name="budget_info",
        attribute="budget_info",
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )
    management_ip = fields.Field(
        column_name="management_ip",
        attribute="management_ip",
        widget=IPManagementWidget(model=networks.IPAddress),
    )
    # no need for str field - management_ip will be exported as str
    management_ip._skip_str_field = True

    class Meta:
        model = physical.DataCenterAsset
        select_related = (
            "model__manufacturer",
            "model__category",
            "service_env__service",
            "service_env__environment",
            "rack__server_room__data_center",
            "configuration_path",
            "property_of",
            "parent",
            "budget_info",
        )
        prefetch_related = (
            "tags",
            "ethernet_set__ipaddress",
            "parent__ethernet_set__ipaddress",
        )
        exclude = ("content_type", "asset_ptr", "baseobject_ptr", "connections")

    def dehydrate_depreciation_rate(self, dc_asset):
        return str(dc_asset.depreciation_rate)

    def _get_management_ip(self, dc_asset):
        if dc_asset:
            # find first management_ip here
            # notice that dc_asset.management_ip property could not be used
            # here, because it will omit prefetch_related cache
            for eth in dc_asset.ethernet_set.all():
                try:
                    if eth.ipaddress and eth.ipaddress.is_management:
                        return eth.ipaddress
                except physical.IPAddress.DoesNotExist:
                    pass

    def dehydrate_parent_str(self, dc_asset) -> str:
        try:
            return dc_asset.parent._str_with_type
        except AttributeError:
            return ""

    def dehydrate_management_ip(self, dc_asset):
        return str(self._get_management_ip(dc_asset))

    def dehydrate_parent_management_ip(self, dc_asset):
        return str(self._get_management_ip(dc_asset.parent))


class ConnectionResource(RalphModelResource):
    outbound = fields.Field(
        column_name="outbound",
        attribute="outbound",
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    inbound = fields.Field(
        column_name="outbound",
        attribute="outbound",
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )

    class Meta:
        model = physical.Connection


class LicenceResource(ResourceWithPrice, RalphModelResource):
    manufacturer = fields.Field(
        column_name="manufacturer",
        attribute="manufacturer",
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    licence_type = fields.Field(
        column_name="licence_type",
        attribute="licence_type",
        widget=ImportedForeignKeyWidget(LicenceType),
    )
    software = fields.Field(
        column_name="software",
        attribute="software",
        widget=ImportedForeignKeyWidget(Software),
    )
    region = fields.Field(
        column_name="region",
        attribute="region",
        widget=ImportedForeignKeyWidget(Region),
    )
    office_infrastructure = fields.Field(
        column_name="office_infrastructure",
        attribute="office_infrastructure",
        widget=ImportedForeignKeyWidget(OfficeInfrastructure),
    )
    users = ThroughField(
        column_name="users",
        attribute="users",
        widget=UserManyToManyWidget(model=LicenceUser),
        through_model=LicenceUser,
        through_from_field_name="licence",
        through_to_field_name="user",
    )
    base_objects = ThroughField(
        column_name="base_objects",
        attribute="baseobjectlicence_set",
        widget=ManyToManyThroughWidget(
            model=BaseObjectLicence,
            related_model=base.BaseObject,
            through_field="base_object",
        ),
        through_model=BaseObjectLicence,
        through_from_field_name="licence",
        through_to_field_name="base_object",
    )
    service_uid = fields.Field(
        column_name="service_uid",
        attribute="service_env",
        widget=AssetServiceUidWidget(assets.ServiceEnvironment),
    )

    class Meta:
        model = Licence
        prefetch_related = ("tags",)
        exclude = (
            "content_type",
            "baseobject_ptr",
        )

    def get_queryset(self):
        return Licence.objects_used_free_with_related.all()

    service_uid._skip_str_field = True


class SupportTypeResource(RalphModelResource):
    class Meta:
        model = SupportType


class SupportResource(ResourceWithPrice, RalphModelResource):
    support_type = fields.Field(
        column_name="support_type",
        attribute="support_type",
        widget=ImportedForeignKeyWidget(SupportType),
    )
    base_objects = ThroughField(
        column_name="base_objects",
        attribute="baseobjectssupport_set",
        widget=ManyToManyThroughWidget(
            model=BaseObjectsSupport,
            related_model=base.BaseObject,
            through_field="baseobject",
        ),
        through_model=BaseObjectsSupport,
        through_from_field_name="support",
        through_to_field_name="baseobject",
    )
    region = fields.Field(
        column_name="region",
        attribute="region",
        widget=ImportedForeignKeyWidget(Region),
    )
    budget_info = fields.Field(
        column_name="budget_info",
        attribute="budget_info",
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )
    property_of = fields.Field(
        column_name="property_of",
        attribute="property_of",
        widget=ImportedForeignKeyWidget(assets.AssetHolder),
    )
    assigned_objects_count = fields.Field(
        readonly=True,
        column_name="assigned_objects_count",
        attribute="assigned_objects_count",
    )

    class Meta:
        model = Support
        exclude = (
            "content_type",
            "baseobject_ptr",
        )
        prefetch_related = ("tags",)

    def get_queryset(self):
        return Support.objects_with_related.all()

    def dehydrate_assigned_objects_count(self, support):
        # this somehow ignores readonly flag, throwing AttributeError during
        # import, but we need it only for export
        try:
            return support.assigned_objects_count
        except AttributeError:
            pass


class ProfitCenterResource(RalphModelResource):
    business_segment = fields.Field(
        column_name="business_segment",
        attribute="business_segment",
        widget=ImportedForeignKeyWidget(assets.BusinessSegment),
    )

    class Meta:
        model = assets.ProfitCenter


class ServiceResource(RalphModelResource):
    profit_center = fields.Field(
        column_name="profit_center",
        attribute="profit_center",
        widget=ImportedForeignKeyWidget(assets.ProfitCenter),
    )
    business_owners = fields.Field(
        column_name="business_owners",
        attribute="business_owners",
        widget=UserManyToManyWidget(get_user_model()),
    )
    technical_owners = fields.Field(
        column_name="technical_owners",
        attribute="technical_owners",
        widget=UserManyToManyWidget(get_user_model()),
    )
    environments = ThroughField(
        column_name="environments",
        attribute="environments",
        widget=widgets.ManyToManyWidget(model=assets.Environment),
        through_model=assets.ServiceEnvironment,
        through_from_field_name="service",
        through_to_field_name="environment",
    )

    class Meta:
        model = assets.Service


class ServiceEnvironmentResource(RalphModelResource):
    service = fields.Field(
        column_name="service",
        attribute="service",
        widget=ImportedForeignKeyWidget(assets.Service),
    )
    environment = fields.Field(
        column_name="environment",
        attribute="environment",
        widget=ImportedForeignKeyWidget(assets.Environment),
    )

    class Meta:
        model = assets.ServiceEnvironment


class BaseObjectLicenceResource(RalphModelResource):
    licence = fields.Field(
        column_name="licence",
        attribute="licence",
        widget=ImportedForeignKeyWidget(Licence),
    )
    base_object = fields.Field(
        column_name="base_object",
        attribute="base_object",
        widget=BaseObjectWidget(base.BaseObject),
    )

    class Meta:
        model = BaseObjectLicence


class LicenceUserResource(RalphModelResource):
    licence = fields.Field(
        column_name="licence",
        attribute="licence",
        widget=ImportedForeignKeyWidget(Licence),
    )
    user = fields.Field(
        column_name="user",
        attribute="user",
        widget=UserWidget(get_user_model()),
    )

    class Meta:
        model = LicenceUser


class BaseObjectsSupportResource(RalphModelResource):
    support = fields.Field(
        column_name="support",
        attribute="support",
        widget=ImportedForeignKeyWidget(Support),
    )
    baseobject = fields.Field(
        column_name="baseobject",
        attribute="baseobject",
        widget=BaseObjectWidget(base.BaseObject),
    )

    class Meta:
        model = BaseObjectsSupport


class BaseObjectsSupportRichResource(RalphModelResource):
    price_per_object = fields.Field(
        column_name="support__price_per_object",
    )

    class Meta:
        model = BaseObjectsSupport
        fields = (
            "support__contract_id",
            "support__support_type",
            "support__serial_no",
            "support__name",
            "support__price",
            "price_per_object",
            "support__date_from",
            "support__date_to",
            "support__description",
            "support__invoice_no",
            "support__invoice_date",
            "support__property_of",
            "support__budget_info",
            "baseobject__asset__hostname",
            "baseobject__asset__barcode",
            "baseobject__asset__sn",
            "baseobject__asset__model",
            "baseobject__service_env",
            "baseobject__configuration_path",
        )

    # def get_queryset(self):
    #     return (
    #         super()
    #         .get_queryset()
    #         .annotate(objects_count=Count("support__baseobjectssupport"))
    #     )

    def dehydrate_price_per_object(self, bo_support):
        support = bo_support.support
        price = getattr(support.price, "amount", Decimal("0.00"))
        return str(
            round(price / bo_support.objects_count, 2)
            if bo_support.objects_count > 0
            else Decimal("0.00")
        )


class RackAccessoryResource(RalphModelResource):
    accessory = fields.Field(
        column_name="accessory",
        attribute="accessory",
        widget=ImportedForeignKeyWidget(physical.Accessory),
    )
    rack = fields.Field(
        column_name="rack",
        attribute="rack",
        widget=ImportedForeignKeyWidget(physical.Rack),
    )

    class Meta:
        model = physical.RackAccessory


class RegionResource(RalphModelResource):
    users = fields.Field(
        column_name="users",
        attribute="users",
        widget=UserManyToManyWidget(get_user_model()),
    )

    class Meta:
        model = Region


class AssetHolderResource(RalphModelResource):
    class Meta:
        model = assets.AssetHolder


class OfficeInfrastructureResource(RalphModelResource):
    class Meta:
        model = OfficeInfrastructure


class BudgetInfoResource(RalphModelResource):
    class Meta:
        model = assets.BudgetInfo


class DomainContractResource(ResourceWithPrice, RalphModelResource):
    domain = fields.Field(
        column_name="domain",
        attribute="domain",
        widget=widgets.ForeignKeyWidget(Domain, "name"),
    )

    class Meta:
        model = DomainContract


class DomainResource(RalphModelResource):
    business_segment = fields.Field(
        column_name="business_segment",
        attribute="business_segment",
        widget=widgets.ForeignKeyWidget(
            assets.BusinessSegment,
            "name",
        ),
    )
    business_owner = fields.Field(
        column_name="business_owner",
        attribute="business_owner",
        widget=UserWidget(get_user_model()),
    )
    technical_owner = fields.Field(
        column_name="technical_owner",
        attribute="technical_owner",
        widget=UserWidget(get_user_model()),
    )
    domain_holder = fields.Field(
        column_name="domain_holder",
        attribute="domain_holder",
        widget=widgets.ForeignKeyWidget(assets.AssetHolder),
    )
    service_env = fields.Field(
        column_name="service_env",
        attribute="service_env",
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment),
    )

    class Meta:
        model = Domain
        exclude = ("baseobject_ptr",)


class OperationTypeResource(RalphModelResource):
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ImportedForeignKeyWidget(OperationType),
    )

    class Meta:
        model = OperationType


class OperationResource(RalphModelResource):
    type = fields.Field(
        column_name="type",
        attribute="type",
        widget=ImportedForeignKeyWidget(OperationType),
    )
    base_objects = fields.Field(
        column_name="base_objects",
        attribute="base_objects",
        widget=widgets.ManyToManyWidget(model=base.BaseObject),
        default=[],
    )
    assignee = fields.Field(
        column_name="assignee",
        attribute="assignee",
        widget=UserWidget(get_user_model()),
    )
    reporter = fields.Field(
        column_name="reporter",
        attribute="reporter",
        widget=UserWidget(get_user_model()),
    )
    service_name = fields.Field(
        column_name="base_objects_service_names",
        attribute="base_objects",
        widget=BaseObjectServiceNamesM2MWidget(model=base.BaseObject),
        default=[],
        readonly=True,
    )
    service_name._skip_str_field = True

    class Meta:
        select_related = ("assignee", "reporter", "type", "status")
        prefetch_related = (
            "tags",
            Prefetch(
                lookup="base_objects",
                queryset=BaseObject.polymorphic_objects.polymorphic_filter(
                    operations__in=Operation.objects.all()
                )
                .select_related(
                    "service_env", "service_env__service", "service_env__environment"
                )
                .polymorphic_select_related(
                    Cluster=["type"], ServiceEnvironment=["service", "environment"]
                ),
            ),
        )
        model = Operation


class ConfigurationModuleResource(RalphModelResource):
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ImportedForeignKeyWidget(configuration.ConfigurationModule),
    )

    class Meta:
        model = configuration.ConfigurationModule


class ConfigurationClassResource(RalphModelResource):
    module = fields.Field(
        column_name="module",
        attribute="module",
        widget=ImportedForeignKeyWidget(configuration.ConfigurationModule),
    )

    class Meta:
        model = configuration.ConfigurationClass


class DCHostResource(RalphModelResource):
    hostname = fields.Field(
        readonly=True,
        column_name="hostname",
        attribute="hostname",
    )
    service_env = fields.Field(
        column_name="service_env",
        attribute="service_env",
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, "name"),
    )
    ips = fields.Field(
        column_name="ip_addresses",
        attribute="ipaddresses",
        widget=widgets.ManyToManyWidget(model=networks.IPAddress),
    )

    class Meta:
        model = hosts.DCHost
        exclude = ("parent",)
